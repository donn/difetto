module top(
    input clk,
    input rstn,
    input si,
    output so,
    input se,
    input tm,
    input[63:0] a,
    input[63:0] b,
    output reg[63:0] c,
    output reg co,
);
    wire[63:0] c_next;
    wire co_next;

    wire carry;    
    wire[31:0] hi_0;
    wire[31:0] hi_1;
    wire co_0, co_1;
    
    wire chain_top_lower, chain_lower_higher0, chain_higher0_higher1;
    
    add32 lower(
        .clk,
        .rstn,
        .si(chain_top_lower),
        .so(chain_lower_higher0),
        .se,
        .tm,
        .ci(1'b0),
        .a(a[31:0]),
        .b(b[31:0]),
        .c(c_next[31:0]),
        .co(carry)
    );
    add32 higher0(
        .clk,
        .rstn,
        .se,
        .si(chain_lower_higher0),
        .so(chain_higher0_higher1),
        .tm,
        .ci(1'b0),
        .a(a[63:32]),
        .b(b[63:32]),
        .c(hi_0),
        .co(co_0)
    );
    add32 higher1(
        .clk,
        .rstn,
        .se,
        .si(chain_higher0_higher1),
        .so,
        .tm,
        .ci(1'b1),
        .a(a[63:32]),
        .b(b[63:32]),
        .c(hi_1),
        .co(co_1)
    );
    assign c_next[63:32] = carry ? hi_1: hi_0;
    assign co_next = carry ? co_1 : co_0;
    
    always @ (posedge clk or negedge rstn)
        if (!rstn) begin
            c <= 64'b0;
            co <= 1'b0;
        end else begin
            c <= c_next;
            co <= co_next;
        end
endmodule
