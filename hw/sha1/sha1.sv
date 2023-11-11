// ------------------------------------------------------
//  Module name: SHA-1
//  Description: SHA-1 block with register inteface
// ------------------------------------------------------

module sha1 #(
    parameter int unsigned DataWidth = 64,
    parameter int unsigned AddrWidth = 32,
    parameter int unsigned DataBytes = DataWidth >> 3,
    parameter bit          ByteAlign = 1
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

    // SHA-1 internal parameters
    localparam int unsigned BlockWidth  = 512;
    localparam int unsigned DigestWidth = 256;

    logic [BlockWidth-1:0] sha_block;

    simple_reg_interface #(
        .DataWidth   ( DataWidth   ),
        .AddrWidth   ( AddrWidth   ),
        .BlockWidth  ( BlockWidth  ),
        .DigestWidth ( DigestWidth ),
        .ByteAlign   ( ByteAlign   )
    ) u_sha1_reg_interface (
        .clk_i,
        .rst_ni,
        .reqdata_i      ( sha_s_reqdata_i   ),
        .reqaddr_i      ( sha_s_reqaddr_i   ),
        .reqvalid_i     ( sha_s_reqvalid_i  ),
        .reqwrite_i     ( sha_s_reqwrite_i  ),
        .reqready_o     ( sha_s_reqready_o  ),
        .reqstrobe_i    ( sha_s_reqstrobe_i ),
        .rspready_i     ( sha_s_rspready_i  ),
        .rspvalid_o     ( sha_s_rspvalid_o  ),
        .rspdata_o      ( sha_s_rspdata_o   ),
        .rsperror_o     ( sha_s_rsperror_o  ),
        .hold_i         (             1'b0  ),
        .idle_i         (             1'b0  ),
        .enable_hash_o  (                   ),
        .reset_hash_o   (                   ),
        .block_o        ( sha_block         ),
        .digest_i       (               '0  ),
        .digest_valid_i (             1'b0  )
    );

    // SHA-1 core
    // ...
    // inputs: sha_block, sha_regsvalid, sha_digestack
    // outputs: digest, digest_valid, (computing ?)

    assign sha_digest_o      = 160'('0);
    assign sha_digestvalid_o = 1'b0;

endmodule
