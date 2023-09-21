// ------------------------------------------------------
//  Module name: sha1
//  Description: sha1 block with register inteface
// ------------------------------------------------------

module sha1 #(
    parameter int unsigned DataWidth = 64,
    parameter int unsigned AddrWidth = 32,
    parameter int unsigned DataBytes = (DataWidth / 8),
    parameter bit ByteAlign = 1
) (
    input  logic                 clk_i,             // Clock
    input  logic                 rst_ni,            // Reset

    input  logic [DataWidth-1:0] sha_s_reqdata_i,   // Data bus request
    input  logic [AddrWidth-1:0] sha_s_reqaddr_i,   // Addr bus request
    input  logic                 sha_s_reqvalid_i,  // Valid requets
    input  logic                 sha_s_reqwrite_i,  // Write request
    output logic                 sha_s_reqready_o,  // Ready signal
    input  logic [DataBytes-1:0] sha_s_reqstrobe_i, // Strobe

    input  logic                 sha_s_rspready_i,  // Response ready
    output logic                 sha_s_rspvalid_o,  // Response valid
    output logic [DataWidth-1:0] sha_s_rspdata_o,   // Data bus response
    output logic                 sha_s_rsperror_o,  // Error response

    input  logic                 sha_process_i,     // Start algorithm pulse
    input  logic                 sha_digestack_i,   // Acknowledge digest
    output logic [159:0]         sha_digest_o,      // Hash digest
    output logic                 sha_digestvalid_o  // Hash digest valid
);

    // Calculate internal parameters
    localparam int unsigned BlockWidth = 512;
    localparam int unsigned NumRegs    = BlockWidth / DataWidth;
    localparam int unsigned Align      = (ByteAlign) ? 8 : 32;
    localparam int unsigned AddrStep   = (BlockWidth / NumRegs) / Align;
    localparam int unsigned AddrBits   = $clog2(NumRegs*AddrStep);

    logic [BlockWidth-1:0]             sha_block;
    logic [NumRegs-1:0][DataWidth-1:0] sha_regs, sha_regs_q;
    logic [NumRegs-1:0]                sha_regssel;

    logic                 reqwrite;
    logic                 reqready;
    logic [DataWidth-1:0] reqdata;
    logic [AddrBits-1:0]  reqaddr;

    logic [AddrWidth-1:0] unused_reqaddr;

    logic                 rsperror;
    logic [DataWidth-1:0] rspdata, rspdata_q;

    // lint
    assign unused_reqaddr = AddrWidth'({'0, sha_s_reqaddr_i[AddrWidth-1:AddrBits]});

    assign reqwrite = sha_s_reqvalid_i & sha_s_reqwrite_i & &sha_s_reqstrobe_i;
    assign reqaddr  = sha_s_reqaddr_i[AddrBits-1:0];
    assign reqready = ~rsperror;

    for (genvar b = 0; b < DataBytes; b++) begin : gen_strobe_mask
        assign reqdata[b*8 +: 8]  = sha_s_reqdata_i[b*8 +: 8] & {8{sha_s_reqstrobe_i[b]}};
    end

    for (genvar r = 0; r < NumRegs; r++) begin : gen_sha_regssel
        assign sha_regssel[r] = (AddrBits'(reqaddr) == AddrBits'(r*AddrStep)) & sha_s_reqvalid_i;
    end

    assign rsperror = ~(|sha_regssel) & reqwrite;

    assign sha_s_rsperror_o = rsperror;
    assign sha_s_rspdata_o  = rspdata;
    assign sha_s_rspvalid_o = sha_s_reqvalid_i & sha_s_rspready_i & |sha_regssel;
    assign sha_s_reqready_o = reqready;

    always_comb begin : sha_regs_wr

        rspdata = rspdata_q;

        for (int r = 0; r < NumRegs; r++) begin
            sha_regs[r] = sha_regs_q[r];
        end

        for (int r = 0; r < NumRegs; r++) begin
            if (sha_regssel[r]) begin
                rspdata = sha_regs_q[r];
                if (reqwrite) begin
                    sha_regs[r] = reqdata;
                end
            end
        end
    end

    always_ff @(posedge clk_i, negedge rst_ni ) begin : sha_regs_ff
        for (int r = 0; r < NumRegs; r++) begin
            if (~rst_ni) begin
                sha_regs_q[r] <= '0;
            end else begin
                sha_regs_q[r] <= sha_regs[r];
            end
        end
    end

    always_ff @(posedge clk_i, negedge rst_ni ) begin : sha_rspdata_ff
        if (~rst_ni) begin
            rspdata_q <= '0;
        end else begin
            rspdata_q <= rspdata;
        end
    end

    // Generate sha1 block
    for (genvar r = 0; r < NumRegs; r++) begin : gen_sha_block
        assign sha_block[r*DataWidth +: DataWidth] = sha_regs_q[r];
    end

    logic sha_regsfixed;
    logic sha_regsvalid, sha_regsvalid_q;

    // TODO: determine how we want to validate the registers when computing the hash value
    assign sha_regsfixed = ~(reqwrite & |sha_regssel);
    assign sha_regsvalid = (sha_process_i | sha_regsvalid_q) & ~sha_regsfixed;

    always_ff @(posedge clk_i, negedge rst_ni ) begin : sha_regsvalid_ff
        if (~rst_ni) begin
            sha_regsvalid_q <= 1'b0;
        end else begin
            sha_regsvalid_q <= sha_regsvalid;
        end
    end

    // sha1 core
    // ...
    // inputs: sha_block, sha_regsvalid, sha_digestack
    // outputs: digest, digest_valid, (computing ?)

    assign sha_digest_o      = 160'('0);
    assign sha_digestvalid_o = 1'b0;

endmodule
