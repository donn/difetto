// SPDX-FileCopyrightText: © 2025 XXX Authors
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

`include "cmd.vh"

`define TAP_TCK     2
`define TAP_TMS     3
`define TAP_TDO     4
`define TAP_TDI     5

`define ULPI_DATA0  6
`define ULPI_DATA1  7
`define ULPI_DATA2  8
`define ULPI_DATA3  9
`define ULPI_DATA4  10
`define ULPI_DATA5  11
`define ULPI_DATA6  12
`define ULPI_DATA7  13
`define ULPI_DIR    14
`define ULPI_NXT    15
`define ULPI_STP    16

module chess_core (
    `ifdef USE_POWER_PINS
    inout  wire VDD,
    inout  wire VSS,
    `endif
    
    input  wire        clk60,     // clock
    input  wire        rst_n,     // reset (active low)
    input  wire        gateware_reset,

    input  wire        usb_rx_valid,
    input  wire [7:0]  usb_rx_data,
    input  wire        usb_rx_next,

    output reg         usb_tx_valid,
    output reg  [7:0]  usb_tx_data,
    input  wire        usb_tx_ready,
);

    wire [7:0] board_data_out;

    reg  [2:0] state_mode;
    reg  [1:0] mask_mode;
    reg        wtm;
    reg  [3:0] write_bus;
    reg  [5:0] ss1;
    reg        ss1_valid;
    reg  [5:0] ss2;
    reg        ss2_valid;

    board b (
        .clk(clk60),
        .rst_n(!gateware_reset),

        .state_mode(state_mode),
        .mask_mode(mask_mode),
        .wtm(wtm),
        .write_bus(write_bus),
        .ss1(ss1),
        .ss1_valid(ss1_valid),
        .ss2(ss2),
        .ss2_valid(ss2_valid),

        .data_out(board_data_out[6:0]),
        .illegal(board_data_out[7])
    );

    reg [7:0] stored_command;

    reg [3:0] state;
    always_ff @(posedge clk60 or posedge gateware_reset) begin
        if (gateware_reset) begin
            usb_tx_data  <= 8'd0;
            usb_tx_valid <= 1'b0;

            state_mode  <= `SM_IDLE;
            mask_mode   <= `MM_NO_CHANGE;
            wtm         <= 0;
            write_bus   <= 0;
            ss1         <= 0;
            ss1_valid   <= 0;
            ss2         <= 0;
            ss2_valid   <= 0;

            stored_command <= 0;

            state       <= 0;
        end else begin
            casez (state)
            0: begin
                usb_tx_data <= 8'b0;
                usb_tx_valid <= 1'b0;
                if (usb_rx_next) begin
                    // Commands:
                    // 0000 000x: SET-WTM
                    // 0000 001x: ? 
                    // 0000 010x: SET-SS1-VALID
                    // 0000 011x: SET-SS2-VALID
                    // 0000 10xx: SET-MASK-MODE
                    // 0000 11xx: ?
                    // 0001 0xxx: SET-STATE-MODE
                    // 0001 1xxx: SET-CORE (elsewhere)
                    // 0010 xxxx: SET-WRITE-BUS
                    // 0011 xxxx: ?

                    // 0100 0000: GET-WTM
                    // 0100 0010: GET-STATUS
                    // 0100 0100: GET-SS1
                    // 0100 0101: GET-SS2
                    // 0100 0110: ?
                    // 0100 0111: ?
                    // 0100 1000: GET-MASK-MODE
                    // 0101 0000: GET-STATE-MODE
                    // 0110 0000: GET-WRITE-BUS
                    // 01xx xxxx: ?
                    //
                    // 10ss ssss: SET-SS1
                    //
                    // 11ss ssss: SET-SS2

                    casez (usb_rx_data[7:6])
                    2'd0: begin // write commands
                        casez (usb_rx_data[5:0])
                        6'b00000?: wtm        <= usb_rx_data[0];   // set wtm
                        6'b00001?: ;
                        6'b00010?: ss1_valid  <= usb_rx_data[0];   // set ss1_valid
                        6'b00011?: ss2_valid  <= usb_rx_data[0];   // set ss2_valid
                        6'b0010??: mask_mode  <= usb_rx_data[1:0]; // set mask_mode
                        6'b0011??: ;
                        6'b010???: state_mode <= usb_rx_data[2:0]; // set state_mode
                        6'b011???: ;
                        6'b10????: write_bus  <= usb_rx_data[3:0]; // set write_bus
                        6'b11????: ;
                        endcase
                    end
                    2'd1: begin // read commands
                        if (usb_tx_ready) begin
                            usb_tx_valid <= 1'b1;

                            casez (usb_rx_data[5:0])
                            6'b00000?: usb_tx_data <= {7'b0, wtm};        // get wtm
                            6'b00001?: usb_tx_data <= board_data_out;     // get board_data_out
                            6'b000100: usb_tx_data <= {1'b0, ss1_valid, ss1}; // get ss1
                            6'b000101: usb_tx_data <= {1'b0, ss2_valid, ss2}; // get ss2
                            6'b000110: ;
                            6'b000111: ;
                            6'b001???: usb_tx_data <= {6'b0, mask_mode};  // get mask_mode
                            6'b01????: usb_tx_data <= {5'b0, state_mode}; // get state_mode
                            6'b1?????: usb_tx_data <= {4'b0, write_bus};  // get write_bus
                            endcase
                        end else begin
                            stored_command <= usb_rx_data;
                            state <= 1;
                        end
                    end
                    2'd2: begin // set ss1
                        ss1 <= usb_rx_data[5:0];
                    end
                    2'd3: begin // set ss2
                        ss2 <= usb_rx_data[5:0];
                    end

                    endcase
                end
            end
            1: begin // USB TX wait
                if (usb_tx_ready) begin
                    usb_tx_valid <= 1'b1;

                    casez (stored_command[5:0])
                    6'b00000?: usb_tx_data <= {7'b0, wtm};            // get wtm
                    6'b00001?: usb_tx_data <= board_data_out;         // get board_data_out
                    6'b000100: usb_tx_data <= {1'b0, ss1_valid, ss1}; // get ss1
                    6'b000101: usb_tx_data <= {1'b0, ss2_valid, ss2}; // get ss2
                    6'b000110: ;
                    6'b000111: ;
                    6'b001???: usb_tx_data <= {6'b0, mask_mode};      // get mask_mode
                    6'b01????: usb_tx_data <= {5'b0, state_mode};     // get state_mode
                    6'b1?????: usb_tx_data <= {4'b0, write_bus};      // get write_bus
                    endcase

                    state <= 0;
                end
            end
            endcase
        end
    end

endmodule


module chip_core #(
    parameter NUM_INPUT_PADS = 12,
    parameter NUM_BIDIR_PADS = 40,
    parameter NUM_ANALOG_PADS = 2
) (
    `ifdef USE_POWER_PINS
    inout  wire VDD,
    inout  wire VSS,
    `endif
    
    input  wire clk60,     // clock
    input  wire rst_ext_n, // reset (active low)
    
    input  wire [NUM_INPUT_PADS-1:0] input_in,   // Input value
    output wire [NUM_INPUT_PADS-1:0] input_pu,   // Pull-up
    output wire [NUM_INPUT_PADS-1:0] input_pd,   // Pull-down

    input  wire [NUM_BIDIR_PADS-1:0] bidir_in,   // Input value
    output wire [NUM_BIDIR_PADS-1:0] bidir_out,  // Output value
    output wire [NUM_BIDIR_PADS-1:0] bidir_oe,   // Output enable
    output wire [NUM_BIDIR_PADS-1:0] bidir_cs,   // Input type (0=CMOS Buffer, 1=Schmitt Trigger)
    output wire [NUM_BIDIR_PADS-1:0] bidir_sl,   // Slew rate (0=fast, 1=slow)
    output wire [NUM_BIDIR_PADS-1:0] bidir_ie,   // Input enable
    output wire [NUM_BIDIR_PADS-1:0] bidir_pu,   // Pull-up
    output wire [NUM_BIDIR_PADS-1:0] bidir_pd,   // Pull-down

    input tm,
    input sce,
    input sci,
    output sco
);
    // See here for usage: https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/IO/gf180mcu_fd_io/digital.html

    wire       tap_tck, tap_tms, tap_tdi;
    wire [7:0] ulpi_data_i, ulpi_data_o, ulpi_data_oe;
    wire       ulpi_dir, ulpi_nxt, ulpi_stp;

    // Disable pull-up and pull-down for input
    assign input_pu = '0;
    assign input_pd = {12{1'b1}};

    // Set the bidir as output
    assign tap_tck     = bidir_in[`TAP_TCK];
    assign tap_tms     = bidir_in[`TAP_TMS];
    assign tap_tdi     = bidir_in[`TAP_TDI];
    assign ulpi_data_i = bidir_in[`ULPI_DATA7:`ULPI_DATA0];
    assign ulpi_dir    = bidir_in[`ULPI_DIR];
    assign ulpi_nxt    = bidir_in[`ULPI_NXT];

    assign bidir_out = {
        {23{1'b0}},
        ulpi_stp, /* ulpi_nxt */ 1'b0, /* ulpi_dir */ 1'b0, ulpi_data_o,
        /* tap_tdi */ 1'b0, /* tap_tdo */ 1'b0, /* tap_tms */ 1'b0, /* tap_tck */ 1'b0, /* unused */ 2'b0
    };

    assign bidir_oe = {
        {23{1'b1}},
        /* ulpi_stp */ 1'b1, /* ulpi_nxt */ 1'b0, /* ulpi_dir */ 1'b0, ulpi_data_oe,
        /* tap_tdi */ 1'b0, /* tap_tdo */ 1'b1, /* tap_tms */ 1'b0, /* tap_tck */ 1'b0, /* unused */ 2'b0
    };
    assign bidir_cs = '0;
    assign bidir_sl = '0;
    assign bidir_ie = ~bidir_oe;
    assign bidir_pu = '0;
    assign bidir_pd = '0;

    // Synchronise the external reset against the clock.
    reg [7:0] rst;
    wire rst_n;

    genvar i;
    generate 
        for (i = 0; i < 8; i++) begin
            always @(posedge clk60 or negedge rst_ext_n) begin
                if (!rst_ext_n)
                    rst[i] <= 0;
                else if (i == 0)
                    rst[i] <= 1'b1;
                else
                    rst[i] <= rst[i-1];
            end
        end
    endgenerate

    assign rst_n = rst[7];

    wire       usb_rx_valid;
    wire [7:0] usb_rx_data;
    wire       usb_rx_next;

    reg        usb_tx_valid;
    reg  [7:0] usb_tx_data;
    wire       usb_tx_ready;

    wire usb_reset;
    wire gateware_reset = (usb_reset) || !rst_n;

    wire tokenizer__new_token, tokenizer__is_in, tokenizer__is_out;
    wire [3:0] tokenizer__endpoint;

    usb_device device (
        .usb_clk(),
        .usb_rst(!rst_n),

        .ulpi__clk__i(clk60),
        .ulpi__data__i(ulpi_data_i),
        .ulpi__data__o(ulpi_data_o), 
        .ulpi__data__oe(ulpi_data_oe),
        .ulpi__dir__i(ulpi_dir),
        .ulpi__nxt__i(ulpi_nxt),
        .ulpi__stp__o(ulpi_stp),

        .low_speed_only(1'b0),
        .full_speed_only(1'b1),
        .connect(1'b1),
        .reset_detected(usb_reset),
        
        .valid(usb_rx_valid),
        .data(usb_rx_data),
        .next(usb_rx_next),

        .tx__valid(usb_tx_valid),
        .tx__data(usb_tx_data),
        .tx__ready(usb_tx_ready),

        .tokenizer__new_token(tokenizer__new_token),
        .tokenizer__is_in(tokenizer__is_in),
        .tokenizer__is_out(tokenizer__is_out),
        .tokenizer__endpoint(tokenizer__endpoint)
    );

    wire [7:0] tap_insn;
    wire       tap_capture, tap_shift, tap_update;
    wire       tap_user_tdi;
    reg        tap_user_tdo;

    reg [2:0] selected_core;

    wire [71:0] tap_core0_tdo_bus;
    wire        usb_core0_tx_valid;
    wire [7:0]  usb_core0_tx_data;
    chess_core core0 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core0_tx_valid),
        .usb_tx_data(usb_core0_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );

    wire        usb_core1_tx_valid;
    wire [7:0]  usb_core1_tx_data;
    chess_core core1 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core1_tx_valid),
        .usb_tx_data(usb_core1_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );

    wire [71:0] tap_core2_tdo_bus;
    wire        usb_core2_tx_valid;
    wire [7:0]  usb_core2_tx_data;
    chess_core core2 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core2_tx_valid),
        .usb_tx_data(usb_core2_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );

    wire [71:0] tap_core3_tdo_bus;
    wire        usb_core3_tx_valid;
    wire [7:0]  usb_core3_tx_data;
    chess_core core3 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core3_tx_valid),
        .usb_tx_data(usb_core3_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );

    wire        usb_core4_tx_valid;
    wire [7:0]  usb_core4_tx_data;
    chess_core core4 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core4_tx_valid),
        .usb_tx_data(usb_core4_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );

    wire [71:0] tap_core5_tdo_bus;
    wire        usb_core5_tx_valid;
    wire [7:0]  usb_core5_tx_data;
    chess_core core5 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core5_tx_valid),
        .usb_tx_data(usb_core5_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );


    wire        usb_core6_tx_valid;
    wire [7:0]  usb_core6_tx_data;
    chess_core core6 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core6_tx_valid),
        .usb_tx_data(usb_core6_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );


    wire        usb_core7_tx_valid;
    wire [7:0]  usb_core7_tx_data;
    chess_core core7 (
    `ifdef USE_POWER_PINS
        .VDD(VDD),
        .VSS(VSS),
    `endif

        .clk60(clk60),
        .rst_n(rst_n),
        .gateware_reset(gateware_reset),

        .usb_rx_valid(usb_rx_valid),
        .usb_rx_data(usb_rx_data),
        .usb_rx_next(usb_rx_next),

        .usb_tx_valid(usb_core7_tx_valid),
        .usb_tx_data(usb_core7_tx_data),
        .usb_tx_ready(usb_tx_ready)
    );

    wire [63:0] usb_core_tx_data = {usb_core7_tx_data, usb_core6_tx_data, usb_core5_tx_data, usb_core4_tx_data, usb_core3_tx_data, usb_core2_tx_data, usb_core1_tx_data, usb_core0_tx_data};
    wire [7:0] usb_core_tx_valid = {usb_core7_tx_valid, usb_core6_tx_valid, usb_core5_tx_valid, usb_core4_tx_valid, usb_core3_tx_valid, usb_core2_tx_valid, usb_core1_tx_valid, usb_core0_tx_valid};

    assign usb_tx_data = usb_core_tx_data[8*selected_core +: 8];
    assign usb_tx_valid = usb_core_tx_valid[selected_core];

    always_ff @(posedge clk60 or posedge gateware_reset) begin
        if (gateware_reset) begin
            selected_core <= 3'b00;
        end else begin
            if (usb_rx_next) begin
                // Commands:
                // 0001 1xxx: SET-CORE

                if (usb_rx_data[7:3] == 5'b00011)
                    selected_core <= usb_rx_data[2:0];
            end
        end
    end

endmodule

`default_nettype wire
