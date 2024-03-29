// Copyright 2023 - cryptopen contributors 
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

// ------------------------------------------------------
//  Module name: SHA-256
//  Description: SHA-256 top-level with register inteface
// ------------------------------------------------------

module sha256 #(
    parameter int unsigned DataWidth   = 64,
    parameter int unsigned AddrWidth   = 32,
    parameter int unsigned DataBytes   = DataWidth >> 3,
    parameter bit          ByteAlign   = 1,
    parameter int unsigned DigestWidth = 256
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
    output logic                 sha_s_rsperror_o   // Error response
);

    // SHA-256 internal parameters
    localparam int unsigned BlockWidth = 512;

    logic [BlockWidth-1:0] block;

    logic enable_hash;
    logic reset_hash;
    logic idle;
    logic hold;
    logic last;

    logic [DigestWidth-1:0] digest;
    logic                   digest_valid;

    simple_reg_interface #(
        .DataWidth   ( DataWidth   ),
        .AddrWidth   ( AddrWidth   ),
        .BlockWidth  ( BlockWidth  ),
        .DigestWidth ( DigestWidth ),
        .ByteAlign   ( ByteAlign   )
    ) u_sha256_reg_interface (
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
        .hold_i         ( hold              ),
        .idle_i         ( idle              ),
        .enable_hash_o  ( enable_hash       ),
        .reset_hash_o   ( reset_hash        ),
        .last_block_o   ( last              ),
        .block_o        ( block             ),
        .digest_i       ( digest            ),
        .digest_valid_i ( digest_valid      )
    );

    sha256_core #(
        .BlockWidth  ( BlockWidth  ),
        .DigestWidth ( DigestWidth )
    ) u_sha256_core (
        .clk_i,
        .rst_ni,
        .block_i        ( block        ),
        .enable_hash_i  ( enable_hash  ),
        .rst_hash_i     ( reset_hash   ),
        .last_block_i   ( last         ),
        .hold_o         ( hold         ),
        .idle_o         ( idle         ),
        .digest_o       ( digest       ),
        .digest_valid_o ( digest_valid )
    );

endmodule
