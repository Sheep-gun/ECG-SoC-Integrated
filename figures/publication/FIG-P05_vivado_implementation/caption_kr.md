# FIG-P05 Vivado FPGA 구현 결과

## (a) Routed tile placement map

Vivado 2020.2의 Device View는 PDF/SVG 직접 export를 지원하지 않는다. 따라서 GUI 스크린샷을 사용하지 않고, 실제 routed checkpoint에서 각 primitive cell의 tile `GRID_POINT_X/Y`를 Tcl로 추출해 전체 MicroBlaze system과 pure classifier core의 배치 분포를 벡터로 표시했다. 이 그림은 routed placement 데이터의 시각화이며 Vivado Device View 화면을 재현한 그림이라고 주장하지 않는다. FPGA 배치 결과이지 ASIC layout 또는 ASIC post-layout 결과가 아니다.

## (b) MicroBlaze IP Integrator Block Design

MicroBlaze, AXI interconnect, AXI-Lite/AXI-Stream 표본 공급기, SNN ECG accelerator, UART, interrupt controller와 IRQ 연결을 보인다. `microblaze_block_design_vivado_native.pdf/.svg`는 Vivado `write_bd_layout`의 직접 출력이며, publication 파일은 raster 변환 없이 회전 메타데이터와 흰 여백만 정리한 벡터다.

## (c) Worst Setup Timing Path

MicroBlaze 통합 post-route system의 최악 setup path를 Vivado Schematic으로 표시했다. `worst_setup_path_vivado_native.pdf/.svg`는 Vivado `write_schematic`의 직접 출력이다. startpoint는 `qrs_energy_abn_count_reg[3]/C`, endpoint는 `u_final/dec_morphology_reg[29]/D`이며 requirement 10.000 ns, data path delay 9.810 ns, slack 0.097 ns이다.

## 자원과 timing 범위

고정 standalone pure RTL 결과는 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns이다. MicroBlaze 통합 post-route system은 12,494 LUT, 8,494 FF, 16 BRAM36, 3 DSP, WNS 0.097 ns이다. 두 WNS는 서로 다른 구현 범위의 timing closure 근거이며 ECG 한 기록의 처리 지연시간이 아니다.

`vivado_implementation_composite.pdf`는 세 페이지로 구성된다. 1쪽은 routed tile vector map, 2쪽은 Vivado native Block Design, 3쪽은 Vivado native worst setup schematic이다. 세 페이지 모두 스크린샷이나 PNG를 포함하지 않는다.

