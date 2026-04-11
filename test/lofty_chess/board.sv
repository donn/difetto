/*
 * Copyright (c) 2024 Hannah Ravensloft
 * SPDX-License-Identifier: Apache-2.0
 */

/* verilator lint_off UNOPTFLAT */

`default_nettype none

module board #(
    parameter TAP_BASE = 1
) (
    input  wire       clk,
    input  wire       rst_n,

    input  wire [2:0] state_mode,
    input  wire [1:0] mask_mode,
    input  wire       wtm,
    input  wire [3:0] write_bus,
    input  wire [5:0] ss1,
    input  wire       ss1_valid,
    input  wire [5:0] ss2,
    input  wire       ss2_valid,

    output reg  [6:0] data_out,
    output reg        illegal
);

// not all signals are used here.
/* verilator lint_off UNUSEDSIGNAL */
wire [5*64-1:0] north, east, south, west, northeast, southeast, southwest, northwest;
/* verilator lint_on UNUSEDSIGNAL */

wire [2*64-1:0] knight;

wire [3*64-1:0] prio;
wire [1*64-1:0] king;

generate
    genvar SQUARE;
    for (SQUARE = 0; SQUARE < 64; SQUARE = SQUARE + 1) begin:gen_square
        localparam RANK = SQUARE / 8;
        localparam FILE = SQUARE % 8;

        // The following mess is intended to get tooling to discover there is no overlap 
        wire [4:0] north_in, east_in, south_in, west_in, northeast_in, southeast_in, southwest_in, northwest_in;
        wire [1:0] nne_in, nee_in, see_in, sse_in, ssw_in, sww_in, nww_in, nnw_in;

        /* verilator lint_off GENUNNAMED */
        if (RANK < 7)
            assign north_in = south[5*(SQUARE+8) +: 5];
        else
            assign north_in = 5'b0;

        if (FILE < 7)
            assign east_in = west[5*(SQUARE+1) +: 5];
        else
            assign east_in = 5'b0;

        if (RANK > 0)
            assign south_in = north[5*(SQUARE-8) +: 5];
        else
            assign south_in = 5'b0;

        if (FILE > 0)
            assign west_in = east[5*(SQUARE-1) +: 5];
        else
            assign west_in = 5'b0;

        if (RANK < 7 && FILE < 7) 
            assign northeast_in = southwest[5*(SQUARE+9) +: 5];
        else
            assign northeast_in = 5'b0;
        
        if (RANK > 0 && FILE < 7)
            assign southeast_in = northwest[5*(SQUARE-7) +: 5];
        else
            assign southeast_in = 5'b0;

        if (RANK > 0 && FILE > 0)
            assign southwest_in = northeast[5*(SQUARE-9) +: 5];
        else
            assign southwest_in = 5'b0;

        if (RANK < 7 && FILE > 0)
            assign northwest_in = southeast[5*(SQUARE+7) +: 5];
        else
            assign northwest_in = 5'b0;

        if (RANK < 6 && FILE < 7)
            assign nne_in = knight[2*(SQUARE+17) +: 2];
        else
            assign nne_in = 2'b0;

        if (RANK < 7 && FILE < 6)
            assign nee_in = knight[2*(SQUARE+10) +: 2];
        else
            assign nee_in = 2'b0;

        if (RANK > 0 && FILE > 1)
            assign see_in = knight[2*(SQUARE-10) +: 2];
        else
            assign see_in = 2'b0;

        if (RANK > 1 && FILE > 0)
            assign sse_in = knight[2*(SQUARE-17) +: 2];
        else
            assign sse_in = 2'b0;

        if (RANK > 1 && FILE < 7)
            assign ssw_in = knight[2*(SQUARE-15) +: 2];
        else
            assign ssw_in = 2'b0;

        if (RANK > 0 && FILE < 6)
            assign sww_in = knight[2*(SQUARE-6)  +: 2];
        else
            assign sww_in = 2'b0;

        if (RANK < 7 && FILE > 1)
            assign nww_in = knight[2*(SQUARE+6)  +: 2];
        else
            assign nww_in = 2'b0;

        if (RANK < 6 && FILE > 0)
            assign nnw_in = knight[2*(SQUARE+15) +: 2];
        else
            assign nnw_in = 2'b0;
        /* verilator lint_on GENUNNAMED */

        square sq (
            .clk(clk),
            .rst_n(rst_n),

            .square(SQUARE[5:0]),
            .state_mode(state_mode),
            .mask_mode(mask_mode),
            .wtm(wtm),
            .write_bus(write_bus),
            .ss1(ss1_valid && ss1 == SQUARE),
            .ss2(ss2_valid && ss2 == SQUARE),

            .north_in(north_in),
            .east_in(east_in),
            .south_in(south_in),
            .west_in(west_in),
            .northeast_in(northeast_in),
            .southeast_in(southeast_in),
            .southwest_in(southwest_in),
            .northwest_in(northwest_in),
            .nne_in(nne_in),
            .nee_in(nee_in),
            .see_in(see_in),
            .sse_in(sse_in),
            .ssw_in(ssw_in),
            .sww_in(sww_in),
            .nww_in(nww_in),
            .nnw_in(nnw_in),

            .north_out(north[5*SQUARE +: 5]),
            .east_out(east[5*SQUARE +: 5]),
            .south_out(south[5*SQUARE +: 5]),
            .west_out(west[5*SQUARE +: 5]),
            .northeast_out(northeast[5*SQUARE +: 5]),
            .southeast_out(southeast[5*SQUARE +: 5]),
            .southwest_out(southwest[5*SQUARE +: 5]),
            .northwest_out(northwest[5*SQUARE +: 5]),

            .knight_out(knight[2*SQUARE +: 2]),

            .prio(prio[3*SQUARE +: 3]),
            .king(king[SQUARE])
        );
    end
endgenerate

wire [6:0] arb_data_out;

arb arbitrator (
    .priority_(prio),
    .data_out(arb_data_out)
);

always @(posedge clk) begin
    data_out <= arb_data_out;
    illegal <= |king;
end

endmodule
