// ------------------------------------------------------
// Module name: sha512_core
// Description: SHA-512 algorithm and control unit
// ------------------------------------------------------

module sha512_core #(
    parameter int unsigned BlockWidth  = 1024,  // 1024-bit block size for SHA-512
    parameter int unsigned DigestWidth = 512    // 512-bit digest for SHA-512
) (
    input  logic                   clk_i,            // Clock
    input  logic                   rst_ni,           // Reset

    input  logic [BlockWidth-1:0]  block_i,          // SHA-512 block
    input  logic                   enable_hash_i,    // Enable hash algorithm
    input  logic                   rst_hash_i,       // Reset hash algorithm
    output logic                   hold_o,           // Hold state
    output logic                   idle_o,           // Idle state

    output logic [DigestWidth-1:0] sha_digest_o,     // Hash digest
    output logic                   sha_digestvalid_o // Hash digest valid
);

    // Finite state machine to control hashing
    typedef enum logic [1:0] {
        IDLE    = 2'h0,
        HASHING = 2'h1,
        HOLD    = 2'h2,
        DONE    = 2'h3
    } sha_fsm_e;

    // SHA-512/224, SHA-512/256, SHA-384, SHA-512 digest initial values
    localparam longint H0 = (DigestWidth == 224) ? 64'h8c3d37c819544da2
                          : (DigestWidth == 256) ? 64'h22312194fc2bf72c
                          : (DigestWidth == 384) ? 64'hcbbb9d5dc1059ed8
                           /*DigestWidth == 512*/: 64'h6a09e667f3bcc908;

    localparam longint H1 = (DigestWidth == 224) ? 64'h73e1996689dcd4d6
                          : (DigestWidth == 256) ? 64'h9f555fa3c84c64c2
                          : (DigestWidth == 384) ? 64'h629a292a367cd507
                           /*DigestWidth == 512*/: 64'hbb67ae8584caa73b;

    localparam longint H2 = (DigestWidth == 224) ? 64'h1dfab7ae32ff9c82
                          : (DigestWidth == 256) ? 64'h2393b86b6f53b151
                          : (DigestWidth == 384) ? 64'h9159015a3070dd17
                           /*DigestWidth == 512*/: 64'h3c6ef372fe94f82b;

    localparam longint H3 = (DigestWidth == 224) ? 64'h679dd514582f9fcf
                          : (DigestWidth == 256) ? 64'h963877195940eabd
                          : (DigestWidth == 384) ? 64'h152fecd8f70e5939
                           /*DigestWidth == 512*/: 64'ha54ff53a5f1d36f1;

    localparam longint H4 = (DigestWidth == 224) ? 64'h0f6d2b697bd44da8
                          : (DigestWidth == 256) ? 64'h96283ee2a88effe3
                          : (DigestWidth == 384) ? 64'h67332667ffc00b31
                           /*DigestWidth == 512*/: 64'h510e527fade682d1;

    localparam longint H5 = (DigestWidth == 224) ? 64'h77e36f7304c48942
                          : (DigestWidth == 256) ? 64'hbe5e1e2553863992
                          : (DigestWidth == 384) ? 64'h8eb44a8768581511
                           /*DigestWidth == 512*/: 64'h9b05688c2b3e6c1f;

    localparam longint H6 = (DigestWidth == 224) ? 64'h3f9d85a86a1d36c8
                          : (DigestWidth == 256) ? 64'h2b0199fc2c85b8aa
                          : (DigestWidth == 384) ? 64'hdb0c2e0d64f98fa7
                           /*DigestWidth == 512*/: 64'h1f83d9abfb41bd6b;

    localparam longint H7 = (DigestWidth == 224) ? 64'h1112e6ad91d692a1
                          : (DigestWidth == 256) ? 64'h0eb72ddc81c52ca2
                          : (DigestWidth == 384) ? 64'h47b5481dbefa4fa4
                           /*DigestWidth == 512*/: 64'h5be0cd19137e2179;


    // K constant used by the four algorithms
    longint K[80] = {
        64'h428a2f98d728ae22,
        64'h7137449123ef65cd,
        64'hb5c0fbcfec4d3b2f,
        64'he9b5dba58189dbbc,
        64'h3956c25bf348b538,
        64'h59f111f1b605d019,
        64'h923f82a4af194f9b,
        64'hab1c5ed5da6d8118,
        64'hd807aa98a3030242,
        64'h12835b0145706fbe,
        64'h243185be4ee4b28c,
        64'h550c7dc3d5ffb4e2,
        64'h72be5d74f27b896f,
        64'h80deb1fe3b1696b1,
        64'h9bdc06a725c71235,
        64'hc19bf174cf692694,
        64'he49b69c19ef14ad2,
        64'hefbe4786384f25e3,
        64'hfc19dc68b8cd5b5,
        64'h240ca1cc77ac9c65,
        64'h2de92c6f592b0275,
        64'h4a7484aa6ea6e483,
        64'h5cb0a9dcbd41fbd4,
        64'h76f988da831153b5,
        64'h983e5152ee66dfab,
        64'ha831c66d2db43210,
        64'hb00327c898fb213f,
        64'hbf597fc7beef0ee4,
        64'hc6e00bf33da88fc2,
        64'hd5a79147930aa725,
        64'h6ca6351e003826f,
        64'h142929670a0e6e70,
        64'h27b70a8546d22ffc,
        64'h2e1b21385c26c926,
        64'h4d2c6dfc5ac42aed,
        64'h53380d139d95b3df,
        64'h650a73548baf63de,
        64'h766a0abb3c77b2a8,
        64'h81c2c92e47edaee6,
        64'h92722c851482353b,
        64'ha2bfe8a14cf10364,
        64'ha81a664bbc423001,
        64'hc24b8b70d0f89791,
        64'hc76c51a30654be30,
        64'hd192e819d6ef5218,
        64'hd69906245565a910,
        64'hf40e35855771202a,
        64'h106aa07032bbd1b8,
        64'h19a4c116b8d2d0c8,
        64'h1e376c085141ab53,
        64'h2748774cdf8eeb99,
        64'h34b0bcb5e19b48a8,
        64'h391c0cb3c5c95a63,
        64'h4ed8aa4ae3418acb,
        64'h5b9cca4f7763e373,
        64'h682e6ff3d6b2b8a3,
        64'h748f82ee5defb2fc,
        64'h78a5636f43172f60,
        64'h84c87814a1f0ab72,
        64'h8cc702081a6439ec,
        64'h90befffa23631e28,
        64'ha4506cebde82bde9,
        64'hbef9a3f7b2c67915,
        64'hc67178f2e372532b,
        64'hca273eceea26619c,
        64'hd186b8c721c0c207,
        64'heada7dd6cde0eb1e,
        64'hf57d4f7fee6ed178,
        64'h6f067aa72176fba,
        64'ha637dc5a2c898a6,
        64'h113f9804bef90dae,
        64'h1b710b35131c471b,
        64'h28db77f523047d84,
        64'h32caab7b40c72493,
        64'h3c9ebe0a15c9bebc,
        64'h431d67c49c100d4c,
        64'h4cc5d4becb3e42b6,
        64'h597f299cfc657e2a,
        64'h5fcb6fab3ad6faec,
        64'h6c44198c4a475817
    };

    // SHA-512 function to compute new words
    function automatic logic [63:0] fword(input logic [BlockWidth-1:0] block, logic [6:0] cntr);
        int idx0 = ~(32'(cntr) - 15) & 32'hf;
        int idx1 = ~(32'(cntr) - 7) & 32'hf;
        int idx2 = ~(32'(cntr) - 2) & 32'hf;
        int idx3 = ~(32'(cntr) - 16) & 32'hf;

        longint w0 = block[idx0 << 6 +: 64];
        longint w1 = block[idx1 << 6 +: 64];
        longint w2 = block[idx2 << 6 +: 64];
        longint w3 = block[idx3 << 6 +: 64];

        longint word0 = {w0[0], w0[63:1]}
                      ^ {w0[7:0], w0[63:8]}
                      ^ w0 >> 7;

        longint word1 = {w2[18:0], w2[63:19]}
                      ^ {w2[60:0], w2[63:61]}
                      ^ w2 >> 6;

        logic [63:0] word;

        word = w3 + word0 + w1 + word1;

        return word;

    endfunction : fword

    // detect end of message
    function automatic logic eom(input logic [63:0] word);
        logic eom = 1'b0;
        for(int b = 0; b < 8; b++) begin
            eom |= (word[b*8 +: 8] == 8'h80);
        end
    endfunction : eom

    logic [BlockWidth-1:0] word_mem, word_mem_q;

    logic eom_captured, eom_captured_q;
    logic eom_flag;
    logic hash_flag, hash_flag_q;
    logic unset_hash_flag;

    logic enable_hash, rst_hash;

    logic [6:0]  round_cntr, round_cntr_q;

    logic [63:0] h0, h1, h2, h3, h4, h5, h6, h7;
    logic [63:0] a, b, c, d, e, f, g, h, k;
    logic [63:0] a_q, b_q, c_q, d_q, e_q, f_q, g_q, h_q;
    logic [63:0] maj, ch, s0, s1, t0, t1;
    logic [63:0] word;

    sha_fsm_e current_state, next_state;

    logic [511:0] digest, digest_q;
    logic         digest_valid, digest_valid_q;
    logic         round_done;
    logic         round_16;
    logic         len_bound;

    // hash main control bits
    assign enable_hash = enable_hash_i;
    assign rst_hash    = rst_hash_i;

    // round is between cycles 16 and 80
    assign round_16 = |round_cntr_q[6:4];
    // end of message must be before 896th bit
    assign len_bound = (round_cntr_q[3:0] inside {4'hf, 4'he});
    // detect end of message byte
    assign eom_flag = eom(word);
    // round counter == 80
    assign round_done = round_cntr_q[6] & round_cntr_q[4];
    // flag meaning an additional hash cycle is required
    assign hash_flag = (eom_flag & len_bound) | hash_flag_q & ~unset_hash_flag;

    // values used during hashing
    assign k   = K[round_cntr_q[6:0]];
    assign maj = (a_q & b_q) ^ (a_q & c_q) ^ (b_q & c_q);
    assign ch  = (e_q & f_q) ^ (~e_q & g_q);
    assign s0  = {a_q[27:0], a_q[63:28]} ^ {a_q[33:0], a_q[63:34]} ^ {a_q[38:0], a_q[63:39]};
    assign s1  = {e_q[13:0], e_q[63:14]} ^ {e_q[17:0], e_q[63:18]} ^ {e_q[40:0], e_q[63:41]};
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
                        word = word_mem[~round_cntr_q[3:0]*64 +: 64];
                        // last cycle if byte 0x80 is seen in range
                        eom_captured |= eom_flag;
                    end else begin
                        // memory efficient : we recalculate the next rounds words during hashing
                        // however this approach is less performant because it requires much more computation
                        word = fword(word_mem, round_cntr);
                        word_mem[~round_cntr[3:0]*64 +: 64] = word;
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
    // digest valid bit and digest on 512, 384, 256 or 224 bits
    assign sha_digestvalid_o = digest_valid_q;
    assign sha_digest_o      = digest_q[511:512-DigestWidth];

endmodule
