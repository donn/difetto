module _4bitadder(
    input clk,
    input rstn,
    input[3:0] a,
    input[3:0] b,
    output[3:0] c,
    input tm,
    input sci,
    input sce,
    output sco
);
    reg[3:0] delay;
    wire[3:0] delay_next = a + b;
    
    assign c = delay;
    
    always @ (posedge clk or negedge rstn)
        if (!rstn)
            delay <= 4'b0;
        else
            delay <= delay_next;
endmodule
