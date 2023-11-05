// ------------------------------------------------------
//  Module name: apb_reg_interface
//  Description: APB compliant register interface that
//               outputs a block to be computed. This
//               interface is a Completer.
// ------------------------------------------------------

module apb_reg_interface #(
    parameter int unsigned DataWidth   = 64,
    parameter int unsigned AddrWidth   = 32,
    parameter int unsigned DataBytes   = DataWidth >> 3,
    parameter int unsigned BlockWidth  = 512,
    parameter int unsigned DigestWidth = 256,
    parameter bit          ByteAlign   = 1
) (
    input  logic                   ppclk_i,       // Clock
    input  logic                   preset_ni,     // Reset

    // From Requester
    input  logic [DataWidth-1:0]   pwdata_c_i,    // Write data
    input  logic [AddrWidth-1:0]   paddr_c_i,     // Address
    input  logic                   psel_c_i,      // Select
    input  logic                   penable_c_i,   // Valid request
    input  logic                   pwrite_c_i,    // Direction (Write or Read)
    input  logic [DataBytes-1:0]   pstrb_c_i,     // Write strobe

    // Towards Requester
    output logic [DataWidth-1:0]   prdata_c_o,    // Read data
    output logic                   pslverr_c_o,   // Transfer error
    output logic                   pready_c_o,    // Ready

    // Internal signals
    input  logic                   hold_i,        // Hold hash
    input  logic                   idle_i,        // Idle state
    output logic                   enable_hash_o, // Enable hash control
    output logic                   reset_hash_o,  // Reset hash control
    output logic [BlockWidth-1:0]  block_o        // Compute block
    input  logic [DigestWidth-1:0] digest_i,      // Digest block
    input  logic                   digest_valid_i // Digest block valid
);

    // Declare offsets on a 4 kB range
    // CTRLADDR   --> 0x000
    // BLOCKADDR  --> 0x100
    // DIGESTADDR --> 0x200
    typedef enum logic [3:0] {
        CTRLADDR   = 4'h0,
        BLOCKADDR  = 4'h1,
        DIGESTADDR = 4'h2
    } offsets_e;

    // control register
    typedef struct packed {
        logic idle;
        logic hold;
        logic enable;
        logic reset;
        logic valid;
    } ctrlreg_t;

    // Address alignment on byte or words
    localparam int unsigned Align = (ByteAlign) ? 8 : 32;

    // Block registers constants
    localparam int unsigned BlRegs     = BlockWidth / DataWidth;
    localparam int unsigned BlAddrStep = (BlockWidth / BlRegs) / Align;

    // Calculate closest multiple of DataWidth
    localparam int unsigned DiPadded = int'($ceil(DigestWidth / DataWidth) + 1) * DataWidth;

    // Digest registers base constant
    localparam int unsigned DiNumRegs  = DiPadded / DataWidth;
    localparam int unsigned DiAddrStep = (DiPadded / DiNumRegs) / Align;

    logic [BlockWidth-1:0]  block;
    logic [DiPadded-1:0]    digest;

    logic [BlRegs-1:0][DataWidth-1:0] block_regs, block_regs_q;
    logic [BlRegs-1:0]                block_regssel;

    logic [DiNumRegs-1:0] digest_regssel;

    logic                 reqwrite;
    logic [DataBytes-1:0] bytewren;
    logic                 reqready, reqready_q;
    logic [11:0]          reqaddr;
    offsets_e             offset;
    logic                 ctrlregwr;
    logic                 ctrlregsel;

    logic unset_enable;

    ctrlreg_t ctrlreg, ctrlreg_q;

    logic [AddrWidth-1:0] unused_reqaddr;

    logic                 rsperror, rsperror_q;
    logic [DataWidth-1:0] rspdata, rspdata_q;

    // lint
    assign unused_reqaddr = AddrWidth'({'0, paddr_c_i[AddrWidth-1:12]});

    assign reqwrite = penable_c_i & pwrite_c_i;
    assign reqready = psel_c_i & ~rsperror_q;
    assign reqaddr  = paddr_c_i[11:0];
    assign offset   = offsets_e'(paddr_c_i[11:8]);

    // block register
    for (genvar r = 0; r < BlRegs; r++) begin : gen_block_regssel
        assign block_regssel[r] = (reqaddr[7:0] == 8'(r*BlAddrStep)) & penable_c_i;
    end

    // digest register
    assign digest = DiPadded'({'0, digest_i});

    for (genvar d = 0; d < DiNumRegs; d++) begin : gen_digest_regssel
        assign digest_regssel[d] = (reqaddr[7:0] == 8'(d*DiAddrStep)) & penable_c_i;
    end

    // control register
    assign ctrlregsel = reqaddr == 12'({CTRLADDR, '0});
    assign ctrlregwr  = ctrlregsel & reqwrite & bytewren[0];

    // read only bits
    assign ctrlreg.idle  = idle_i;
    assign ctrlreg.hold  = hold_i;
    assign ctrlreg.valid = digest_valid_i;

    assign unset_enable = idle_i | hold_i | digest_valid_i | ctrlreg_q.reset;

    // read / write bits
    assign ctrlreg.enable = (ctrlregwr) ?
                            pwdata_c_i[0]
                          : ctrlreg_q.enable & ~unset_enable;
    assign ctrlreg.reset  = (ctrlregwr) ? pwdata_c_i[1] : 1'b0;

    always_ff @(posedge pclk_i, negedge preset_ni) begin : ctrlreg_ff
        if (~preset_ni) begin
            ctrlreg_q <= '0;
        end else begin
            ctrlreg_q <= ctrlreg;
        end
    end

    assign enable_hash_o = ctrlreg_q.enable;
    assign reset_hash_o  = ctrlreg_q.reset;

    assign pslverr_c_o = rsperror_q;
    assign prdata_c_o  = rspdata_q;

    assign pready_c_o = reqready_q;

    for (genvar b = 0; b < DataBytes; b++) begin : gen_byte_wren
        assign bytewren[b] = pstrb_c_i[b] & reqwrite;
    end

    always_comb begin : regs_wr

        rspdata = rspdata_q;

        rsperror  = 1'b0;

        for (int r = 0; r < BlRegs; r++) begin
            block_regs[r] = block_regs_q[r];
        end

        case (offset)

            CTRLADDR: begin

                if (ctrlregsel) begin
                    rspdata = '0;

                    rspdata[0] = ctrlreg_q.enable;
                    rspdata[1] = ctrlreg_q.reset;
                    rspdata[2] = ctrlreg_q.idle;
                    rspdata[3] = ctrlreg_q.hold;
                    rspdata[4] = ctrlreg_q.valid;
                end

                rsperror = ~ctrlregsel & penable_c_i;

            end

            BLOCKADDR: begin

                for (int r = 0; r < BlRegs; r++) begin
                    if (block_regssel[r]) begin
                        rspdata = block_regs_q[r];
                        for (int b = 0; b < DataBytes; b++) begin
                            block_regs[r][b*8 +: 8] = (bytewren[b]) ?
                                                      pwdata_c_i[b*8 +: 8]
                                                    : block_regs_q[r][b*8 +: 8];
                        end
                    end
                end

                rsperror = ~(|block_regssel) & penable_c_i;

            end

            DIGESTADDR: begin

                for (int d = 0; d < DiNumRegs; d++) begin
                    if (digest_regssel[d]) begin
                        rspdata = DataWidth'({'0, digest[DataWidth*d +: DataWidth]});
                    end
                end

                rsperror = ~(|digest_regssel) & penable_c_i;

            end

            default: rsperror = penable_c_i;

        endcase

    end

    always_ff @(posedge pclk_i, negedge preset_ni) begin : block_regs_ff
        for (int r = 0; r < BlRegs; r++) begin
            if (~preset_ni) begin
                block_regs_q[r] <= '0;
            end else begin
                block_regs_q[r] <= block_regs[r];
            end
        end
    end

    always_ff @(posedge pclk_i, negedge preset_ni) begin : bus_ff
        if (~preset_ni) begin
            rspdata_q  <= '0;
            rsperror_q <= 1'b0;
            reqready_q <= 1'b0;
        end else begin
            rspdata_q  <= rspdata;
            rsperror_q <= rsperror;
            reqready_q <= reqready;
        end
    end

    // Generate block
    for (genvar r = 0; r < BlRegs; r++) begin : gen_block
        assign block[r*DataWidth +: DataWidth] = block_regs_q[r];
    end

    assign block_o = block;

endmodule
