// ------------------------------------------------------
//  Module name: prim_generic_rotl
//  Description: Rotate left operation
// ------------------------------------------------------

module prim_generic_rotl #(
    parameter int unsigned Width = 32,
    parameter int unsigned Position = 1
) (
    input  logic [Width-1:0] in0_i,
    output logic [Width-1:0] rotl_o
);

    // n is the number of right shifts, this is the Position modulo the Width
    // To prevent misbehavior of the module (when Position > Width)
    localparam n = Position % Width;

    assign rotl_o = (in0_i << n) | (in0_i >> Width - n);

endmodule