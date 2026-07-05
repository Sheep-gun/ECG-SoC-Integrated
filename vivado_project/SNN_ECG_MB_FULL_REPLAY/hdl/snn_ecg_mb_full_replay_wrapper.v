//Copyright 1986-2020 Xilinx, Inc. All Rights Reserved.
//--------------------------------------------------------------------------------
//Tool Version: Vivado v.2020.2 (win64) Build 3064766 Wed Nov 18 09:12:45 MST 2020
//Date        : Mon Jul  6 04:15:31 2026
//Host        : DESKTOP-F81OJT8 running 64-bit major release  (build 9200)
//Command     : generate_target snn_ecg_mb_full_replay_wrapper.bd
//Design      : snn_ecg_mb_full_replay_wrapper
//Purpose     : IP block netlist
//--------------------------------------------------------------------------------
`timescale 1 ps / 1 ps

module snn_ecg_mb_full_replay_wrapper
   (CLK100MHZ,
    CPU_RESETN,
    UART_RXD_OUT,
    UART_TXD_IN);
  input CLK100MHZ;
  input CPU_RESETN;
  output UART_RXD_OUT;
  input UART_TXD_IN;

  wire CLK100MHZ;
  wire CPU_RESETN;
  wire UART_RXD_OUT;
  wire UART_TXD_IN;

  snn_ecg_mb_full_replay snn_ecg_mb_full_replay_i
       (.CLK100MHZ(CLK100MHZ),
        .CPU_RESETN(CPU_RESETN),
        .UART_RXD_OUT(UART_RXD_OUT),
        .UART_TXD_IN(UART_TXD_IN));
endmodule
