// Copyright 2023 - cryptopen contributors 
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

// ------------------------------------------------------
//  Module name: SHA-1 core
//  Description: SHA-1 algorithm and control unit
// ------------------------------------------------------

module sha1_core #(
    parameter int unsigned BlockWidth  = 512,
    parameter int unsigned DigestWidth = 160
) (
    input  logic                   clk_i,            // Clock
    input  logic                   rst_ni,           // Reset

    input  logic [BlockWidth-1:0]  block_i,          // sha block
    input  logic                   enable_hash_i,    // Enable hash algorithm
    input  logic                   rst_hash_i,       // Reset hash algorithm
    output logic                   hold_o,           // Hold state
    output logic                   idle_o,           // Idle state

    output logic [DigestWidth-1:0] digest_o,         // Hash digest
    output logic                   digest_valid_o    // Hash digest valid
);

    // finite state machine to control hashing
    typedef enum logic [1:0] {
        IDLE    = 2'h0,
        HASHING = 2'h1,
        HOLD    = 2'h2,
        DONE    = 2'h3
    } sha_fsm_e;

    localparam int WordSize = 32;
    localparam int NumWords = BlockWidth / WordSize;

    // SHA-1 digest initial values
    integer H0 = 32'h67452301;
    integer H1 = 32'hefcdab89;
    integer H2 = 32'h98badcfe;
    integer H3 = 32'h10325476;
    integer H4 = 32'hc3d2e1f0;

    // SHA-1 function to compute new words
    function automatic logic [31:0] hword(input logic [BlockWidth-1:0] block, logic [6:0] cntr);
        int idx0 = (32'(cntr) - 3) & 32'hf;
        int idx1 = (32'(cntr) - 8) & 32'hf;
        int idx2 = (32'(cntr) - 14) & 32'hf;
        int idx3 = (32'(cntr) - 16) & 32'hf;

        int w0 = block[idx0 << 5 +: 32];
        int w1 = block[idx1 << 5 +: 32];
        int w2 = block[idx2 << 5 +: 32];
        int w3 = block[idx3 << 5 +: 32];

        int temp_word = w0 ^ w1 ^ w2 ^ w3;

        logic [31:0] word;

        word = {temp_word[30:0], temp_word[31]};

        return word;

    endfunction : hword

    // detect end of message
    function automatic logic eom(input logic [31:0] word);
        logic e = 1'b0;
        for(int b = 0; b < 4; b++) begin
            e |= (word[b*8 +: 8] == 8'h80);
        end
        return e;
    endfunction : eom

    logic [BlockWidth-1:0] word_mem, word_mem_q;

    logic eom_captured, eom_captured_q;
    logic eom_flag;
    logic hash_flag, hash_flag_q;
    logic unset_hash_flag;

    logic enable_hash, rst_hash;

    logic [6:0]  round_cntr, round_cntr_q;

    logic [31:0] h0, h1, h2, h3, h4;
    logic [31:0] a, b, c, d, e;
    logic [31:0] a_q, b_q, c_q, d_q, e_q;
    logic [31:0] f, k, t0, t1;
    logic [31:0] word;

    sha_fsm_e current_state, next_state;

    logic [DigestWidth-1:0] digest, digest_q;

    logic         digest_valid, digest_valid_q;
    logic         round_done;
    logic         round_16;
    logic         len_bound;

    // hash main control bits
    assign enable_hash = enable_hash_i;
    assign rst_hash    = rst_hash_i;

    // round is between cycles 16 and 80
    assign round_16 = |round_cntr_q[6:4];
    // end of message must be before 448th bit
    assign len_bound = (round_cntr_q[6:0] inside {7'he, 7'hf});
    // detect end of message byte
    assign eom_flag = eom(word);
    // round counter == 64
    assign round_done = round_cntr_q[6] & round_cntr_q[4];
    // flag meaning an additional hash cycle is required
    assign hash_flag = (eom_flag & len_bound) | hash_flag_q & ~unset_hash_flag;

    // values used during hashing
    assign t0  = {a_q[26:0], a_q[31:27]};
    assign t1  = (t0 + f + e_q + k + word);

    always_comb begin : sha_control

        next_state   = current_state;
        round_cntr   = round_cntr_q;
        digest_valid = digest_valid_q;
        word_mem     = word_mem_q;

        eom_captured    = eom_captured_q;
        unset_hash_flag = 1'b0;

        word = '0;
        f    = '0;
        k    = '0;

        // apply hx values from previous intermediary digest
        {h0, h1, h2, h3, h4} = digest_q;

        a = a_q;
        b = b_q;
        c = c_q;
        d = d_q;
        e = e_q;

        case (current_state)

            IDLE: begin

                // idle state resets all intermediary values and counters
                // also accept a new block until we start hashing

                h0 = H0;
                h1 = H1;
                h2 = H2;
                h3 = H3;
                h4 = H4;

                a = H0;
                b = H1;
                c = H2;
                d = H3;
                e = H4;

                digest_valid = 1'b0;
                round_cntr   = '0;

                for (int w = 0; w < NumWords; w++) begin
                    word_mem[w*WordSize +: WordSize] = block_i[(NumWords-w)*WordSize-1 -: WordSize];
                end

                eom_captured = 1'b0;

                // start hashing next cycle if enabled
                if (enable_hash & ~rst_hash) begin
                    next_state = HASHING;
                end

            end

            HASHING: begin

                // hashing state performs the main computation each cycle

                // reset takes precedence, back to idle state
                if (rst_hash) begin
                    next_state = IDLE;
                // if enable bit is deasserted, go to hold state to halt computation
                end else if (~enable_hash) begin
                    next_state = HOLD;
                // round is done, go to hold or done depending on message length
                end else if (round_done) begin
                    round_cntr = '0;

                    {h0, h1, h2, h3, h4} = {
                        h0 + a_q,
                        h1 + b_q,
                        h2 + c_q,
                        h3 + d_q,
                        h4 + e_q
                    };

                    {a, b, c, d, e} = {
                        h0,
                        h1,
                        h2,
                        h3,
                        h4
                    };

                    next_state = (eom_captured & ~hash_flag) ? DONE : HOLD;
                // else continue the computation
                end else begin

                    if (~round_16) begin
                        word = word_mem[round_cntr_q[3:0]*32 +: 32];
                        // last cycle if byte 0x80 is seen in range
                        eom_captured |= eom_flag;
                    end else begin
                        // memory efficient : we recalculate the next rounds words during hashing
                        // however this approach is less performant because it requires much more computation
                        word = hword(word_mem, round_cntr);
                        word_mem[round_cntr[3:0]*32 +: 32] = word;
                    end

                    if (round_cntr_q <= 19) begin
                        k = 32'h5a827999;
                        f = (b_q & c_q) ^ (~b_q & d_q);
                    end else if ((round_cntr_q >= 20) && (round_cntr_q <= 39)) begin
                        k = 32'h6ed9eba1;
                        f = b_q ^ c_q ^ d_q;
                    end else if ((round_cntr_q >= 40) && (round_cntr_q <= 59)) begin
                        k = 32'h8f1bbcdc;
                        f = (b_q & c_q) ^ (b_q & d_q) ^ (c_q & d_q);
                    end else if (round_cntr_q >= 60) begin
                        k = 32'hca62c1d6;
                        f = b_q ^ c_q ^ d_q;
                    end

                    {a, b, c, d, e} = {
                        t1,
                        a_q,
                        {b_q[1:0], b_q[31:2]},
                        c_q,
                        d_q
                    };

                    // increment round counter by 1
                    round_cntr = round_cntr + 1;

                end

            end

            HOLD: begin

                // hold state
                // in this state, computed values are stored
                // user can modify the block in the registers during the rounds
                // and start the computation again based on previous digest value

                unset_hash_flag = 1'b1;

                // reset takes precedence, back to idle state
                if (rst_hash) begin
                    next_state = IDLE;
                // if enable, accept block input and go to hashing
                end else if (enable_hash) begin
                    for (int w = 0; w < NumWords; w++) begin
                        word_mem[w*WordSize +: WordSize] = block_i[(NumWords-w)*WordSize-1 -: WordSize];
                    end
                    next_state = HASHING;
                end

            end

            DONE: begin

                // done state
                // computation is over based on the message length

                // assert digest is valid
                digest_valid    = 1'b1;
                eom_captured    = 1'b0;
                unset_hash_flag = 1'b1;

                // next move has to be a reset since computation is done
                if (rst_hash) begin
                    next_state = IDLE;
                end

            end

            default: next_state = IDLE;

        endcase
    end

    always_ff @(posedge clk_i, negedge rst_ni) begin : sha_fsm_ff
        if (~rst_ni) begin
            current_state  <= IDLE;
            round_cntr_q   <= '0;
            eom_captured_q <= 1'b0;
            hash_flag_q    <= 1'b0;
            a_q            <= H0;
            b_q            <= H1;
            c_q            <= H2;
            d_q            <= H3;
            e_q            <= H4;
        end else begin
            current_state  <= next_state;
            round_cntr_q   <= round_cntr;
            eom_captured_q <= eom_captured;
            hash_flag_q    <= hash_flag;
            a_q            <= a;
            b_q            <= b;
            c_q            <= c;
            d_q            <= d;
            e_q            <= e;
        end
    end

    always_ff @(posedge clk_i, negedge rst_ni) begin : word_mem_ff
        if (~rst_ni) begin
            word_mem_q  <= '0;
        end else begin
            word_mem_q  <= word_mem;
        end
    end

    // assemble the raw digest value
    assign digest = {h0, h1, h2, h3, h4};

    // additional information for control register
    assign hold_o = (current_state == HOLD);
    assign idle_o = (current_state == IDLE);

    always_ff @(posedge clk_i, negedge rst_ni) begin : digest_ff
        if (~rst_ni) begin
            digest_q       <= '0;
            digest_valid_q <= 1'b0;
        end else begin
            digest_q       <= digest;
            digest_valid_q <= digest_valid;
        end
    end

    // user available data is computed here
    // digest valid bit and digest on 256 bits
    assign digest_valid_o = digest_valid_q;
    assign digest_o       = digest_q[DigestWidth-1:0];

endmodule
