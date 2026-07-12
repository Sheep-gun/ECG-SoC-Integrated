# FIG-P05 Vivado FPGA 구현 결과

**(a) Post-route Device View.** Vivado 2020.2에서 `xc7a100tcsg324-1`의 routed checkpoint를 연 전체 FPGA fabric 화면이다. magenta 영역은 MicroBlaze 통합 system 안의 pure classifier core hierarchy를 강조한 것이다. 이 화면은 FPGA placement/routing 결과이며 ASIC layout, transistor-level layout 또는 post-layout ASIC 검증이 아니다.

**(b) MicroBlaze IP Integrator Block Design.** MicroBlaze, AXI interconnect, AXI-Lite/AXI-Stream sample feeder, SNN ECG accelerator, UART, interrupt controller와 IRQ 연결을 보인다. Vivado의 `write_bd_layout`로 실제 block design에서 export하였다.

**(c) Worst Setup Timing Path.** post-route MicroBlaze 통합 system의 최악 setup path를 Vivado Schematic View에 표시하였다. startpoint는 `qrs_energy_abn_count_reg[3]/C`, endpoint는 `u_final/dec_morphology_reg[29]/D`이며, requirement 10.000 ns, data path delay 9.810 ns, slack 0.097 ns이다. 이는 통합 system의 timing path이며, pure RTL standalone 구현의 WNS 8.184 ns와는 다른 구현 범위다.

**(d) Resource/Timing Summary.** 고정 standalone pure RTL 결과는 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns이다. 재생성한 MicroBlaze 통합 post-route system은 12,494 LUT, 8,494 FF, 16 BRAM36, 3 DSP, WNS 0.097 ns이며, 그 안의 SNN AXI wrapper는 10,485 LUT와 6,652 FF를 사용한다. 두 WNS는 timing closure 근거이지 ECG 한 기록의 처리 지연시간이 아니다.

확대 파일 `device_view_accelerator_zoom.png`는 실제 Vivado Device View에서 accelerator가 선택된 영역을 crop·확대한 것이며 배치 정보를 다시 그리거나 합성하지 않았다.

