// ----------------------------------------------------------
//  Module name: axi4lite_reg_interface
//  Description: AXI4-Lite compliant slave register interface
//               that outputs a block to be computed and
//               control signals.
// ---------------------------------s------------------------

module axi4_reg_interface #(
    parameter int unsigned DataWidth  = 32,
    parameter int unsigned AddrWidth  = 32,
    parameter int unsigned DataBytes  = DataWidth >> 3,
    parameter int unsigned BlockWidth = 512,
    parameter bit          ByteAlign  = 1
) (
    input  logic                  aclk_i,        // Clock
    input  logic                  areset_ni,     // Reset

    // Write address channel
    input  logic                  awvalid_s_i,   // Valid write address
    output logic                  awready_s_o,   // Slave address ready
    input  logic [AddrWidth-1:0]  awaddr_s_i,    // Write address
    input  logic [2:0]            awprot_s_i,    // Write privilege level

    // Write data channel
    input  logic                  wvalid_s_i,    // Valid write data
    output logic                  wready_s_o,    // Slave data ready
    input  logic [DataWidth-1:0]  wdata_s_i,     // Write data
    input  logic [DataBytes-1:0]  wstrb_s_i,     // Write data strobe

    // Write response channel
    output logic                  bvalid_s_o,    // Valid write response
    input  logic                  bready_s_i,    // Master response ready
    output logic                  bresp_s_o,     // Write transaction status

    // Read address channel
    input  logic                  arvalid_s_i,   // Valud read address
    output logic                  arready_s_o,   // Slave read ready
    input  logic [AddrWidth-1:0]  araddr_s_i,    // Read address
    input  logic [2:0]            arprot_s_o,    // Read privilege level

    // Read data channel
    output logic                  rvalid_s_o,    // Valid read data
    input  logic                  rready_s_i,    // Master read ready
    output logic [DataWidth-1:0]  rdata_s_o,     // Read data
    output logic                  rresp_s_o,     // Read transfer status

    // Internal signals
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

    localparam bit AXI4Compliant = 1'b1;

    // Calculate control register address
    localparam int unsigned Offset       = (1 << AddrBits);
    localparam int unsigned CtrlRegAddr  = Offset;
    localparam int unsigned CtrlAddrBits = AddrBits + 1;

    // Control register structure
    typedef struct packed {
        logic idle;
        logic hold;
        logic enable;
        logic reset;
        logic bus_axi4;
    } shactrlreg_t;

    // Response signalling
    typedef enum logic [1:0] {
        OKAY   = 2'h0,
        EXOKAY = 2'h1,
        SLVERR = 2'h2,
        DECERR = 2'h3
    } sha_fsm_e;

    logic [BlockWidth-1:0]             block;
    logic [NumRegs-1:0][DataWidth-1:0] regs, regs_q;
    logic [NumRegs-1:0]                regssel;

    logic                 reqwrite;
    logic [DataBytes-1:0] bytewren;
    logic [AddrBits-1:0]  reqaddr;

    logic [AddrBits:0]    ctrlreqaddr;
    logic                 ctrlreq;
    logic                 ctrlreqwr;
    logic                 ctrlreqsel;
    logic                 ctrlrsperror;

    shactrlreg_t ctrlreg, ctrlreg_q;

    logic [AddrWidth-1:0] unused_reqaddr;

    logic                 rspvalid, rspvalid_q;
    logic                 rsperror, rsperror_q;
    logic [DataWidth-1:0] rspdata, rspdata_q;

    // lint
    assign unused_reqaddr = AddrWidth'({'0, awaddr_s_i[AddrWidth-1:CtrlAddrBits]});

    assign reqwrite = wvalid_s_i;

    // block register
    assign reqaddr  = awaddr_s_i[AddrBits-1:0];

    for (genvar r = 0; r < NumRegs; r++) begin : gen_regssel
        assign regssel[r] = (AddrBits'(reqaddr) == AddrBits'(r*AddrStep)) & wvalid_s_i & ~ctrlreq;
    end

    // control register
    assign ctrlreqaddr = awaddr_s_i[AddrBits:0];
    assign ctrlreq     = awaddr_s_i[AddrBits];
    assign ctrlreqwr   = ctrlreq & reqwrite & bytewren[0];
    assign ctrlreqsel  = ctrlreqaddr == CtrlAddrBits'(CtrlRegAddr);

    // read only bits
    assign ctrlreg.idle    = idle_i;
    assign ctrlreg.hold    = hold_i;
    assign ctrlreg.bus_axi4 = AXI4Compliant;

    // read / write bits
    assign ctrlreg.enable = (ctrlreqwr) ?
                            wdata_i[0]
                          : ctrlreg_q.enable & ~(idle_i | hold_i | ctrlreg_q.reset);
    assign ctrlreg.reset  = (ctrlreqwr) ? wdata_i[1] : 1'b0;

    always_ff @(posedge aclk_i, negedge areset_ni) begin : ctrlreg_ff
        if (~areset_ni) begin
            ctrlreg_q <= '0;
        end else begin
            ctrlreg_q <= ctrlreg;
        end
    end

    assign enable_hash_o = ctrlreg_q.enable;
    assign reset_hash_o  = ctrlreg_q.reset;

    assign rsperror = ~(|regssel) & ctrlrsperror & reqwrite;
    assign rspvalid = wvalid_s_i & wready_o & (|regssel | ctrlreqsel);

    /* assign pslverr_c_o = rsperror_q;
    assign prdata_c_o  = rspdata_q;
    assign pready_c_o  = rspvalid_q; */

    for (genvar b = 0; b < DataBytes; b++) begin : gen_byte_wren
        assign bytewren[b] = wstrb_s_i[b] & wvalid_s_i;
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
                    regs[r][b*8 +: 8] = (bytewren[b]) ? wdata_i[b*8 +: 8]
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
            rspdata[6] = ctrlreg_q.bus_axi4;

        end else begin
            ctrlrsperror = 1'b1;
        end
    end

    always_ff @(posedge aclk_i, negedge areset_ni) begin : regs_ff
        for (int r = 0; r < NumRegs; r++) begin
            if (~areset_ni) begin
                regs_q[r] <= '0;
            end else begin
                regs_q[r] <= regs[r];
            end
        end
    end

    always_ff @(posedge aclk_i, negedge areset_ni) begin : rspdata_ff
        if (~areset_ni) begin
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
