// ------------------------------------------------------
//  Module name: prim_generic_parity
//  Description: Parity function
// ------------------------------------------------------

module prim_generic_parity #(
    parameter int unsigned Width = 32
) (
    input  logic [Width-1:0] in0_i,
    input  logic [Width-1:0] in1_i,
    input  logic [Width-1:0] in2_i,
    output logic [Width-1:0] parity_o
);

    assign parity_o = in0_i ^ in1_i ^ in2_i;

endmodule