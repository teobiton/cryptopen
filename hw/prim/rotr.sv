// ------------------------------------------------------
//  Module name: prim_generic_rotr
//  Description: Rotate right operation
// ------------------------------------------------------

module prim_generic_rotr #(
    parameter int unsigned Width = 32
    parameter int unsigned Position = 1
) (
    input  logic [Width-1:0] in0_i,
    output logic [Width-1:0] rotr_o
);

    // n is the number of right shifts, this is the Position modulo the Width
    // To prevent misbehavior of the module (when Position > Width)
    localparam n = Position % Width;

    assign rotr_o = (in0_i >> n) | (in0_i << Width - n);

endmodule