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
    
    \$dff  #(.WIDTH(WIDTH), .CLK_POLARITY(CLK_POLARITY)) _store_ (
        .CLK(CLK),
        .D(Q),
        .Q(store)
    );
    
    assign Q = (TEST == TEST_POLARITY) ? store : D;
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
