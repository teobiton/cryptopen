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
    input  logic                  clk_i,             // Clock
    input  logic                  rst_ni,            // Reset

    input  logic [DataWidth-1:0]  reqdata_i,   // Data bus request
    input  logic [AddrWidth-1:0]  reqaddr_i,   // Addr bus request
    input  logic                  reqvalid_i,  // Valid requets
    input  logic                  reqwrite_i,  // Write request
    output logic                  reqready_o,  // Ready signal
    input  logic [DataBytes-1:0]  reqstrobe_i, // Strobe

    input  logic                  rspready_i,  // Response ready
    output logic                  rspvalid_o,  // Response valid
    output logic [DataWidth-1:0]  rspdata_o,   // Data bus response
    output logic                  rsperror_o,  // Error response

    output logic [BlockWidth-1:0] block_o      // Compute block
);

    // Calculate internal parameters
    localparam int unsigned NumRegs  = BlockWidth / DataWidth;
    localparam int unsigned Align    = (ByteAlign) ? 8 : 32;
    localparam int unsigned AddrStep = (BlockWidth / NumRegs) / Align;
    localparam int unsigned AddrBits = $clog2(NumRegs*AddrStep);

    logic [BlockWidth-1:0]             block;
    logic [NumRegs-1:0][DataWidth-1:0] regs, regs_q;
    logic [NumRegs-1:0]                regssel;

    logic                 reqwrite;
    logic [DataBytes-1:0] bytewren;
    logic                 reqready;
    logic [AddrBits-1:0]  reqaddr;

    logic [AddrWidth-1:0] unused_reqaddr;

    logic                 rsperror;
    logic [DataWidth-1:0] rspdata, rspdata_q;

    // lint
    assign unused_reqaddr = AddrWidth'({'0, reqaddr_i[AddrWidth-1:AddrBits]});

    assign reqwrite = reqvalid_i & reqwrite_i;
    assign reqaddr  = reqaddr_i[AddrBits-1:0];
    assign reqready = ~rsperror;

    for (genvar r = 0; r < NumRegs; r++) begin : gen_regssel
        assign regssel[r] = (AddrBits'(reqaddr) == AddrBits'(r*AddrStep)) & reqvalid_i;
    end

    assign rsperror = ~(|regssel) & reqwrite;

    assign rsperror_o = rsperror;
    assign rspdata_o  = rspdata;
    assign rspvalid_o = reqvalid_i & rspready_i & |regssel;
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
    end

    always_ff @(posedge clk_i, negedge rst_ni ) begin : regs_ff
        for (int r = 0; r < NumRegs; r++) begin
            if (~rst_ni) begin
                regs_q[r] <= '0;
            end else begin
                regs_q[r] <= regs[r];
            end
        end
    end

    always_ff @(posedge clk_i, negedge rst_ni ) begin : rspdata_ff
        if (~rst_ni) begin
            rspdata_q <= '0;
        end else begin
            rspdata_q <= rspdata;
        end
    end

    // Generate sha1 block
    for (genvar r = 0; r < NumRegs; r++) begin : gen_block
        assign block[r*DataWidth +: DataWidth] = regs_q[r];
    end

    assign block_o = block;

endmodule
