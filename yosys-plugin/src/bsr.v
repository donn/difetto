(* no_boundary_scan *)
(* keep_hierarchy *)
module _difetto_ibsr(CLK, TEST, D, Q);
    parameter WIDTH = 32'd1;
    parameter CLK_POLARITY = 1'b1;
    parameter TEST_POLARITY = 1'b1;
    
    input CLK;
    input TEST;
    input [WIDTH-1:0] D;
    output [WIDTH-1:0] Q;
    
    wire [WIDTH-1:0] store;
    
    genvar ai;
    generate
        if (CLK_POLARITY) begin : rising
            for (ai = 0; ai < WIDTH; ai = ai + 1) begin : bits
                \$_DFF_P_ _store_ (
                    .C(CLK),
                    .D(Q[ai]),
                    .Q(store[ai])
                );
            end
        end else begin : falling
            for (ai = 0; ai < WIDTH; ai = ai + 1) begin : bits
                \$_DFF_N_ _store_ (
                    .C(CLK),
                    .D(Q[ai]),
                    .Q(store[ai])
                );
            end
        end
    endgenerate

    \$mux #(.WIDTH(WIDTH)) _mux_ (
        .S(TEST == TEST_POLARITY),
        .A(D),
        .B(store),
        .Y(Q)
    );
endmodule

(* no_boundary_scan *)
module _difetto_ibsr_dummy(CLK, TEST, D, Q);
    parameter WIDTH = 1;
    parameter CLK_POLARITY = 1'b1;
    parameter TEST_POLARITY = 1'b1;
    
    input CLK;
    input TEST;
    input [WIDTH-1:0] D;
    output [WIDTH-1:0] Q;
    
    assign Q = D;
endmodule

(* no_boundary_scan *)
(* keep_hierarchy *)
module _difetto_obsr(CLK, D, Q);
    parameter WIDTH = 32'd1;
    parameter CLK_POLARITY = 1'b1;
    
    input CLK;
    input [WIDTH-1:0] D;
    output [WIDTH-1:0] Q;
    wire [WIDTH-1:0] _dummy_;
    
    genvar ai;
    generate
        if (CLK_POLARITY) begin : rising
            for (ai = 0; ai < WIDTH; ai = ai + 1) begin : bits
                \$_DFF_P_ _store_ (
                    .C(CLK),
                    .D(D[ai]),
                    .Q(Q[ai])
                );
            end
        end else begin : falling
            for (ai = 0; ai < WIDTH; ai = ai + 1) begin : bits
                \$_DFF_N_ _store_ (
                    .C(CLK),
                    .D(D[ai]),
                    .Q(Q[ai])
                );
            end
        end
    endgenerate
endmodule

(* no_boundary_scan *)
module _difetto_obsr_dummy(CLK, D, Q);
    parameter WIDTH = 1;
    parameter CLK_POLARITY = 1'b1;
    parameter TEST_POLARITY = 1'b1;
    
    input CLK;
    input [WIDTH-1:0] D;
    output [WIDTH-1:0] Q;
    
    assign Q = D;
endmodule
