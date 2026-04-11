/*
 * Copyright (c) 2024 Hannah Ravensloft
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module arb_unit (
    input  wire [2:0] p_lhs,
    input  wire [5:0] s_lhs,
    input  wire [2:0] p_rhs,
    input  wire [5:0] s_rhs,
    output wire [2:0] p_out,
    output wire [5:0] s_out
);

assign p_out = (p_rhs > p_lhs) ? p_rhs : p_lhs;
assign s_out = (p_rhs > p_lhs) ? s_rhs : s_lhs;

endmodule


module arb_layer #(
    parameter WIDTH = 32
) (
    input  wire [6*WIDTH-1:0]  priority_in,
    input  wire [12*WIDTH-1:0] square_in,
    output wire [3*WIDTH-1:0]  priority_out,
    output wire [6*WIDTH-1:0]  square_out
);

generate
    genvar i;
    for (i = 0; i < WIDTH; i = i + 1) begin:arb_layer
        arb_unit arb_i (
            .p_lhs(priority_in[6*i +: 3]),
            .s_lhs(square_in[12*i +: 6]),
            .p_rhs(priority_in[6*i + 3 +: 3]),
            .s_rhs(square_in[12*i + 6 +: 6]),
            .p_out(priority_out[3*i +: 3]),
            .s_out(square_out[6*i +: 6])
        );
    end
endgenerate

endmodule


// Decide the priority for all squares.
module arb (
    input  wire [191:0] priority_,
    output wire [6:0]   data_out
);

wire [383:0] square;

generate
    genvar i;
    for (i = 0; i < 64; i = i + 1) begin:assign_square
        assign square[6*i +: 6] = i;
    end
endgenerate

wire [95:0]  l1_prio;
wire [191:0] l1_sq;

arb_layer #(
    .WIDTH(32)
) l1 (
    .priority_in(priority_),
    .square_in(square),
    .priority_out(l1_prio),
    .square_out(l1_sq)
);

wire [47:0] l2_prio;
wire [95:0] l2_sq;

arb_layer #(
    .WIDTH(16)
) l2 (
    .priority_in(l1_prio),
    .square_in(l1_sq),
    .priority_out(l2_prio),
    .square_out(l2_sq)
);

wire [23:0] l3_prio;
wire [47:0] l3_sq;

arb_layer #(
    .WIDTH(8)
) l3 (
    .priority_in(l2_prio),
    .square_in(l2_sq),
    .priority_out(l3_prio),
    .square_out(l3_sq)
);

wire [11:0] l4_prio;
wire [23:0] l4_sq;

arb_layer #(
    .WIDTH(4)
) l4 (
    .priority_in(l3_prio),
    .square_in(l3_sq),
    .priority_out(l4_prio),
    .square_out(l4_sq)
);

wire [5:0]  l5_prio;
wire [11:0] l5_sq;

arb_layer #(
    .WIDTH(2)
) l5 (
    .priority_in(l4_prio),
    .square_in(l4_sq),
    .priority_out(l5_prio),
    .square_out(l5_sq)
);

wire [2:0]  l6_prio;

arb_layer #(
    .WIDTH(1)
) l6 (
    .priority_in(l5_prio),
    .square_in(l5_sq),
    .priority_out(l6_prio),
    .square_out(data_out[5:0])
);

assign data_out[6] = l6_prio == 0;

endmodule
