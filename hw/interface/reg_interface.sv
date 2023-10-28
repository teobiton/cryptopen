// ------------------------------------------------------
//  Module name: reg_interface
//  Description: generic register interface that outputs
//               a block to be computed
// ------------------------------------------------------

module reg_interface #(
    parameter int unsigned DataWidth  = 64,
    parameter int unsigned AddrWidth  = 32,
    parameter int unsigned DataBytes  = DataWidth >> 3,
    parameter int unsigned BlockWidth = 512,
    parameter bit          ByteAlign  = 1
) (
    input  logic                  clk_i,         // Clock
    input  logic                  rst_ni,        // Reset

    input  logic [DataWidth-1:0]  reqdata_i,     // Data bus request
    input  logic [AddrWidth-1:0]  reqaddr_i,     // Addr bus request
    input  logic                  reqvalid_i,    // Valid requets
    input  logic                  reqwrite_i,    // Write request
    output logic                  reqready_o,    // Ready signal
    input  logic [DataBytes-1:0]  reqstrobe_i,   // Strobe

    input  logic                  rspready_i,    // Response ready
    output logic                  rspvalid_o,    // Response valid
    output logic [DataWidth-1:0]  rspdata_o,     // Data bus response
    output logic                  rsperror_o,    // Error response

    input  logic                  hold_i,        // Hold hash
    input  logic                  idle_i,        // Idle state
    output logic                  enable_hash_o, // Enable hash control
    output logic                  reset_hash_o,  // Reset hash control
    output logic [BlockWidth-1:0] block_o        // Compute block
);

    // Calculate internal parameters
    localparam int unsigned NumRegs  = BlockWidth / DataWidth;
    localparam int unsigned Align    = (ByteAlign) ? 8 : 32;
    localparam int unsigned AddrStep = (BlockWidth / NumRegs) / Align;
    localparam int unsigned AddrBits = $clog2(NumRegs*AddrStep);

    // Calculate control register address
    localparam int unsigned Offset       = (1 << AddrBits);
    localparam int unsigned CtrlRegAddr  = Offset;
    localparam int unsigned CtrlAddrBits = AddrBits + 1;

    logic [BlockWidth-1:0]             block;
    logic [NumRegs-1:0][DataWidth-1:0] regs, regs_q;
    logic [NumRegs-1:0]                regssel;

    logic                 reqwrite;
    logic [DataBytes-1:0] bytewren;
    logic                 reqready;
    logic [AddrBits-1:0]  reqaddr;

    logic [AddrBits:0]    ctrlreqaddr;
    logic                 ctrlreq;
    logic                 ctrlreqwr;
    logic                 ctrlreqsel;
    logic                 ctrlrsperror;

    typedef struct packed {
        logic idle;
        logic hold;
        logic enable;
        logic reset;
    } shactrlreg_t;

    shactrlreg_t ctrlreg, ctrlreg_q;

    logic [AddrWidth-1:0] unused_reqaddr;

    logic                 rsperror;
    logic [DataWidth-1:0] rspdata, rspdata_q;

    // lint
    assign unused_reqaddr = AddrWidth'({'0, reqaddr_i[AddrWidth-1:CtrlAddrBits]});

    assign reqwrite = reqvalid_i & reqwrite_i;
    assign reqready = ~rsperror;

    // block register
    assign reqaddr  = reqaddr_i[AddrBits-1:0];

    for (genvar r = 0; r < NumRegs; r++) begin : gen_regssel
        assign regssel[r] = (AddrBits'(reqaddr) == AddrBits'(r*AddrStep)) & reqvalid_i & ~ctrlreq;
    end

    // control register
    assign ctrlreqaddr = reqaddr_i[AddrBits:0];
    assign ctrlreq     = reqaddr_i[AddrBits];
    assign ctrlreqwr   = ctrlreq & reqwrite & bytewren[0];
    assign ctrlreqsel  = ctrlreqaddr == CtrlAddrBits'(CtrlRegAddr);

    // read only bits
    assign ctrlreg.idle = idle_i;
    assign ctrlreg.hold = hold_i;

    // read / write bits
    assign ctrlreg.enable = (ctrlreqwr) ?
                            reqdata_i[0]
                          : ctrlreg_q.enable & ~(idle_i | hold_i | ctrlreg_q.reset);
    assign ctrlreg.reset  = (ctrlreqwr) ? reqdata_i[1] : 1'b0;

    always_ff @(posedge clk_i, negedge rst_ni) begin : ctrlreg_ff
        if (~rst_ni) begin
            ctrlreg_q <= '0;
        end else begin
            ctrlreg_q <= ctrlreg;
        end
    end

    assign enable_hash_o = ctrlreg_q.enable;
    assign reset_hash_o  = ctrlreg_q.reset;

    assign rsperror = ~(|regssel) & ctrlrsperror & reqwrite;

    assign rsperror_o = rsperror;
    assign rspdata_o  = rspdata;
    assign rspvalid_o = reqvalid_i & rspready_i & (|regssel | ctrlreqsel);
    assign reqready_o = reqready;

    for (genvar b = 0; b < DataBytes; b++) begin : gen_byte_wren
        assign bytewren[b] = reqstrobe_i[b] & reqwrite;
    end

    always_comb begin : regs_wr

        rspdata = rspdata_q;

        for (int r = 0; r < NumRegs; r++) begin
            regs[r] = regs_q[r];
        end

        for (int r = 0; r < NumRegs; r++) begin
            if (regssel[r]) begin
                rspdata = regs_q[r];
                for (int b = 0; b < DataBytes; b++) begin
                    regs[r][b*8 +: 8] = (bytewren[b]) ? reqdata_i[b*8 +: 8]
                                                      : regs_q[r][b*8 +: 8];
                end
            end
        end

        ctrlrsperror = 1'b0;

        if (ctrlreqsel) begin
            rspdata = '0;

            rspdata[0] = ctrlreg_q.enable;
            rspdata[1] = ctrlreg_q.reset;
            rspdata[2] = ctrlreg_q.idle;
            rspdata[3] = ctrlreg_q.hold;

        end else begin
            ctrlrsperror = 1'b1;
        end
    end

    always_ff @(posedge clk_i, negedge rst_ni) begin : regs_ff
        for (int r = 0; r < NumRegs; r++) begin
            if (~rst_ni) begin
                regs_q[r] <= '0;
            end else begin
                regs_q[r] <= regs[r];
            end
        end
    end

    always_ff @(posedge clk_i, negedge rst_ni) begin : rspdata_ff
        if (~rst_ni) begin
            rspdata_q <= '0;
        end else begin
            rspdata_q <= rspdata;
        end
    end

    // Generate sha block
    for (genvar r = 0; r < NumRegs; r++) begin : gen_block
        assign block[r*DataWidth +: DataWidth] = regs_q[r];
    end

    assign block_o = block;

endmodule
