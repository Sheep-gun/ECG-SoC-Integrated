# FIG-P05 Vivado FPGA 구현 결과

## (a) 전체 MicroBlaze 통합 system

Vivado 2020.2의 실제 post-route Device View 위에 고정 routed checkpoint의 hierarchy별 primitive cell tile `GRID_POINT_X/Y`를 정합했다. 자홍색은 SNN ECG accelerator, 노란색은 MicroBlaze, 초록색은 local memory, 주황색은 sample feeder, 파란색은 AXI·UART·interrupt control logic이다. 번호와 색상은 실제 배치 셀을 설명하기 위한 주석이며 기능 블록을 pblock으로 고정했다는 뜻은 아니다.

## (b) SNN accelerator에 속한 배치 셀만 분리 표시

동일한 Device View에서 `snn_ecg_axi_accelerator_0` hierarchy에 속한 placed primitive 좌표만 자홍색으로 강조한다. 이는 별도의 구현이나 다른 칩이 아니라 (a)의 통합 system에서 accelerator 배치만 분리해 읽도록 만든 확대 표시다. 가속기 logic이 하나의 직사각형 영역이 아니라 여러 FPGA logic column에 분산되어 있음을 보여준다.

## (c) 구현 범위와 정량 결과

standalone pure RTL은 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns이다. MicroBlaze 통합 post-route system은 12,494 LUT, 8,494 FF, 16 BRAM, 3 DSP, WNS 0.097 ns이다. 두 결과는 서로 다른 구현 범위이며 ECG 기록의 관찰시간이나 board-level latency를 의미하지 않는다.

## 별도 Figure: MicroBlaze IP Integrator Block Design

MicroBlaze, AXI interconnect, AXI-Lite/AXI-Stream 표본 공급기, SNN ECG accelerator, UART, interrupt controller와 IRQ 연결을 보인다. `microblaze_block_design_vivado_native.pdf/.svg`는 Vivado `write_bd_layout`의 직접 출력이며, publication 파일은 raster 변환 없이 회전 메타데이터와 흰 여백만 정리한 벡터다.

## 별도 Figure: Worst Setup Timing Path

MicroBlaze 통합 post-route system의 최악 setup path를 Vivado Schematic으로 표시했다. `worst_setup_path_vivado_native.pdf/.svg`는 Vivado `write_schematic`의 직접 출력이다. startpoint는 `qrs_energy_abn_count_reg[3]/C`, endpoint는 `u_final/dec_morphology_reg[29]/D`이며 requirement 10.000 ns, data path delay 9.810 ns, slack 0.097 ns이다.

## 자원과 timing 범위

고정 standalone pure RTL 결과는 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns이다. MicroBlaze 통합 post-route system은 12,494 LUT, 8,494 FF, 16 BRAM36, 3 DSP, WNS 0.097 ns이다. 두 WNS는 서로 다른 구현 범위의 timing closure 근거이며 ECG 한 기록의 처리 지연시간이 아니다.

`device_view_annotated_publication.pdf/.svg/.png`는 실제 Device View와 hierarchy 배치 좌표를 결합한 승인 Figure다. 기존 `vivado_implementation_composite.pdf`는 routed tile vector map과 두 native vector를 보존한 3페이지 보조 evidence package다.
