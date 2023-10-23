// ------------------------------------------------------
//  Module name: sha256 core
//  Description: sha256 algorithm and control unit
// ------------------------------------------------------

module sha256_core #(
    parameter int unsigned BlockWidth = 512
) (
    input  logic                  clk_i,            // Clock
    input  logic                  rst_ni,           // Reset

    input  logic [BlockWidth-1:0] block_i,          // sha block
    output logic                  enable_hash_i,    // Enable hash algorith
    output logic                  rst_hash_i,       // Reset hash algorith
    
    output logic [6:0]            round_o,          // Round number (0..79)
    output logic [63:0]           cycle_o,          // Acknowledge digest
    output logic [255:0]          sha_digest_o,     // Hash digest
    output logic                  sha_digestvalid_o // Hash digest valid
);

    // finite state machine to control hashing
    typedef enum logic [2:0] { 
        IDLE    = 3'h0,
        HASHING = 3'h1,
        HOLD    = 3'h2,
        DONE    = 3'h3
    } sha_fsm_e;

    // sha256 and sha224 digest initial values
    integer H0 = 32'h6A09E667;
    integer H1 = 32'hBB67AE85;
    integer H2 = 32'h3C6EF372;
    integer H3 = 32'hA54FF53A;
    integer H4 = 32'h510E527F;
    integer H5 = 32'h9B05688C;
    integer H6 = 32'h1F83D9AB;
    integer H7 = 32'h5BE0CD19;

    // k constant used by sha256 and sha224 algorithm
    integer k[64] = {
        32'h428a2f98,32'h71374491,32'hb5c0fbcf,32'he9b5dba5,32'h3956c25b,32'h59f111f1,32'h923f82a4,32'hab1c5ed5,
        32'hd807aa98,32'h12835b01,32'h243185be,32'h550c7dc3,32'h72be5d74,32'h80deb1fe,32'h9bdc06a7,32'hc19bf174,
        32'he49b69c1,32'hefbe4786,32'h0fc19dc6,32'h240ca1cc,32'h2de92c6f,32'h4a7484aa,32'h5cb0a9dc,32'h76f988da,
        32'h983e5152,32'ha831c66d,32'hb00327c8,32'hbf597fc7,32'hc6e00bf3,32'hd5a79147,32'h06ca6351,32'h14292967,
        32'h27b70a85,32'h2e1b2138,32'h4d2c6dfc,32'h53380d13,32'h650a7354,32'h766a0abb,32'h81c2c92e,32'h92722c85,
        32'ha2bfe8a1,32'ha81a664b,32'hc24b8b70,32'hc76c51a3,32'hd192e819,32'hd6990624,32'hf40e3585,32'h106aa070,
        32'h19a4c116,32'h1e376c08,32'h2748774c,32'h34b0bcb5,32'h391c0cb3,32'h4ed8aa4a,32'h5b9cca4f,32'h682e6ff3,
        32'h748f82ee,32'h78a5636f,32'h84c87814,32'h8cc70208,32'h90befffa,32'ha4506ceb,32'hbef9a3f7,32'hc67178f2
    };

    logic [BlockWidth-1:0] sha_block;
    logic [63:0]           msg_length;
    logic enable_hash, rst_hash;
    
    logic [7:0]  round;
    logic [63:0] cycle;

    sha_fsm_e current_state, next_state;

    always_comb begin : sha_control
        
        next_state = current_state;

        case (current_state) begin
            
            IDLE: begin
            
            end

            HASHING: begin

            end
            
            HOLD: begin

            end

            DONE: begin

            end

        endcase
    end

    always_ff @(posedge clk_i, negedge rst_ni ) begin : sha_fsm_ff
        if (~rst_ni) begin
            current_state <= IDLE;
        end else begin
            current_state <= next_state;
        end
    end

    assign round_o = round;
    assign cycle_o = cycle;
    
    assign sha_digest_o      = digest;
    assign sha_digestvalid_o = digest_valid;

endmodule
