// Copyright 2023 @ cryptopen contributors 
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

// ------------------------------------------------------
//  Module name: SHA-256 core
//  Description: SHA-256 algorithm and control unit
// ------------------------------------------------------

module sha256_core #(
    parameter int unsigned BlockWidth  = 512,
    parameter int unsigned DigestWidth = 256
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

    // SHA-256 and SHA-224 digest initial values
    integer H0 = (DigestWidth == 224) ? 32'hc1059ed8 : 32'h6a09e667;
    integer H1 = (DigestWidth == 224) ? 32'h367cd507 : 32'hbb67ae85;
    integer H2 = (DigestWidth == 224) ? 32'h3070dd17 : 32'h3c6ef372;
    integer H3 = (DigestWidth == 224) ? 32'hf70e5939 : 32'ha54ff53a;
    integer H4 = (DigestWidth == 224) ? 32'hffc00b31 : 32'h510e527f;
    integer H5 = (DigestWidth == 224) ? 32'h68581511 : 32'h9b05688c;
    integer H6 = (DigestWidth == 224) ? 32'h64f98fa7 : 32'h1f83d9ab;
    integer H7 = (DigestWidth == 224) ? 32'hbefa4fa4 : 32'h5be0cd19;

    // K constant used by SHA-256 and SHA-224 algorithms
    integer K[64] = {
        32'h428a2f98, 32'h71374491, 32'hb5c0fbcf, 32'he9b5dba5,
        32'h3956c25b, 32'h59f111f1, 32'h923f82a4, 32'hab1c5ed5,
        32'hd807aa98, 32'h12835b01, 32'h243185be, 32'h550c7dc3,
        32'h72be5d74, 32'h80deb1fe, 32'h9bdc06a7, 32'hc19bf174,
        32'he49b69c1, 32'hefbe4786, 32'h0fc19dc6, 32'h240ca1cc,
        32'h2de92c6f, 32'h4a7484aa, 32'h5cb0a9dc, 32'h76f988da,
        32'h983e5152, 32'ha831c66d, 32'hb00327c8, 32'hbf597fc7,
        32'hc6e00bf3, 32'hd5a79147, 32'h06ca6351, 32'h14292967,
        32'h27b70a85, 32'h2e1b2138, 32'h4d2c6dfc, 32'h53380d13,
        32'h650a7354, 32'h766a0abb, 32'h81c2c92e, 32'h92722c85,
        32'ha2bfe8a1, 32'ha81a664b, 32'hc24b8b70, 32'hc76c51a3,
        32'hd192e819, 32'hd6990624, 32'hf40e3585, 32'h106aa070,
        32'h19a4c116, 32'h1e376c08, 32'h2748774c, 32'h34b0bcb5,
        32'h391c0cb3, 32'h4ed8aa4a, 32'h5b9cca4f, 32'h682e6ff3,
        32'h748f82ee, 32'h78a5636f, 32'h84c87814, 32'h8cc70208,
        32'h90befffa, 32'ha4506ceb, 32'hbef9a3f7, 32'hc67178f2
    };

    // SHA-256 function to compute new words
    function automatic logic [31:0] hword(input logic [BlockWidth-1:0] block, logic [6:0] cntr);
        int idx0 = ~(32'(cntr) - 15) & 32'hf;
        int idx1 = ~(32'(cntr) - 7) & 32'hf;
        int idx2 = ~(32'(cntr) - 2) & 32'hf;
        int idx3 = ~(32'(cntr) - 16) & 32'hf;

        int w0 = block[idx0 << 5 +: 32];
        int w1 = block[idx1 << 5 +: 32];
        int w2 = block[idx2 << 5 +: 32];
        int w3 = block[idx3 << 5 +: 32];

        int word0 = {w0[6:0], w0[31:7]}
                  ^ {w0[17:0], w0[31:18]}
                  ^ w0 >> 3;

        int word1 = {w2[16:0], w2[31:17]}
                  ^ {w2[18:0], w2[31:19]}
                  ^ w2 >> 10;

        logic [31:0] word;

        word = w3 + word0 + w1 + word1;

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

    logic [31:0] h0, h1, h2, h3, h4, h5, h6, h7;
    logic [31:0] a, b, c, d, e, f, g, h, k;
    logic [31:0] a_q, b_q, c_q, d_q, e_q, f_q, g_q, h_q;
    logic [31:0] maj, ch, s0, s1, t0, t1;
    logic [31:0] word;

    sha_fsm_e current_state, next_state;

    logic [255:0] digest, digest_q;
    logic         digest_valid, digest_valid_q;
    logic         round_done;
    logic         round_16;
    logic         len_bound;

    // hash main control bits
    assign enable_hash = enable_hash_i;
    assign rst_hash    = rst_hash_i;

    // round is between cycles 16 and 64
    assign round_16 = |round_cntr_q[5:4];
    // end of message must be before 448th bit
    assign len_bound = (round_cntr_q[3:0] inside {4'hf, 4'he});
    // detect end of message byte
    assign eom_flag = eom(word);
    // round counter == 64
    assign round_done = round_cntr_q[6];
    // flag meaning an additional hash cycle is required
    assign hash_flag = (eom_flag & len_bound) | hash_flag_q & ~unset_hash_flag;

    // values used during hashing
    assign k   = K[round_cntr_q[5:0]];
    assign maj = (a_q & b_q) ^ (a_q & c_q) ^ (b_q & c_q);
    assign ch  = (e_q & f_q) ^ (~e_q & g_q);
    assign s1  = {e_q[5:0], e_q[31:6]} ^ {e_q[10:0], e_q[31:11]} ^ {e_q[24:0], e_q[31:25]};
    assign s0  = {a_q[1:0], a_q[31:2]} ^ {a_q[12:0], a_q[31:13]} ^ {a_q[21:0], a_q[31:22]};
    assign t0  = (h_q + s1 + ch + k + word);
    assign t1  = (s0 + maj);

    always_comb begin : sha_control

        next_state   = current_state;
        round_cntr   = round_cntr_q;
        digest_valid = digest_valid_q;
        word_mem     = word_mem_q;

        eom_captured    = eom_captured_q;
        unset_hash_flag = 1'b0;

        word = '0;

        // apply hx values from previous intermediary digest
        {h0, h1, h2, h3, h4, h5, h6, h7} = digest_q;

        a = a_q;
        b = b_q;
        c = c_q;
        d = d_q;
        e = e_q;
        f = f_q;
        g = g_q;
        h = h_q;

        case (current_state)

            IDLE: begin

                // idle state resets all intermediary values and counters
                // also accept a new block until we start hashing

                h0 = H0;
                h1 = H1;
                h2 = H2;
                h3 = H3;
                h4 = H4;
                h5 = H5;
                h6 = H6;
                h7 = H7;

                a = H0;
                b = H1;
                c = H2;
                d = H3;
                e = H4;
                f = H5;
                g = H6;
                h = H7;

                digest_valid = 1'b0;
                round_cntr   = '0;

                word_mem     = block_i;
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

                    {h0, h1, h2, h3, h4, h5, h6, h7} = {
                        h0 + a_q,
                        h1 + b_q,
                        h2 + c_q,
                        h3 + d_q,
                        h4 + e_q,
                        h5 + f_q,
                        h6 + g_q,
                        h7 + h_q
                    };

                    {a, b, c, d, e, f, g, h} = {
                        h0,
                        h1,
                        h2,
                        h3,
                        h4,
                        h5,
                        h6,
                        h7
                    };

                    next_state = (eom_captured & ~hash_flag) ? DONE : HOLD;
                // else continue the computation
                end else begin

                    if (~round_16) begin
                        word = word_mem[~round_cntr_q[3:0]*32 +: 32];
                        // last cycle if byte 0x80 is seen in range
                        eom_captured |= eom_flag;
                    end else begin
                        // memory efficient : we recalculate the next rounds words during hashing
                        // however this approach is less performant because it requires much more computation
                        word = hword(word_mem, round_cntr);
                        word_mem[~round_cntr[3:0]* 32 +: 32] = word;
                    end

                    {a, b, c, d, e, f, g, h} = {
                        t0 + t1,
                        a_q,
                        b_q,
                        c_q,
                        d_q + t0,
                        e_q,
                        f_q,
                        g_q
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
                    word_mem   = block_i;
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
            digest_valid_q <= 1'b0;
            eom_captured_q <= 1'b0;
            hash_flag_q    <= 1'b0;
            a_q            <= H0;
            b_q            <= H1;
            c_q            <= H2;
            d_q            <= H3;
            e_q            <= H4;
            f_q            <= H5;
            g_q            <= H6;
            h_q            <= H7;
        end else begin
            current_state  <= next_state;
            round_cntr_q   <= round_cntr;
            digest_valid_q <= digest_valid;
            eom_captured_q <= eom_captured;
            hash_flag_q    <= hash_flag;
            a_q            <= a;
            b_q            <= b;
            c_q            <= c;
            d_q            <= d;
            e_q            <= e;
            f_q            <= f;
            g_q            <= g;
            h_q            <= h;
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
    assign digest = {h0, h1, h2, h3, h4, h5, h6, h7};

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
    // digest valid bit and digest on 256 or 224 bits
    assign digest_valid_o = digest_valid_q;
    assign digest_o       = digest_q[255:256-DigestWidth];

endmodule
