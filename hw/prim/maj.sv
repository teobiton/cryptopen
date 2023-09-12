// -----------------------------------------------------
//  Module name: prim_generic_maj
//  Description: Majority function
// -----------------------------------------------------

module prim_generic_maj #(
    parameter int unsigned Width = 32
) (
    input  logic [Width-1:0] in0_i,
    input  logic [Width-1:0] in1_i,
    input  logic [Width-1:0] in2_i,
    output logic [Width-1:0] maj_o
);

    assign maj_o = (in0_i & in1_i)
                 ^ (in0_i & in2_i)
                 ^ (in1_i & in2_i);

endmodule