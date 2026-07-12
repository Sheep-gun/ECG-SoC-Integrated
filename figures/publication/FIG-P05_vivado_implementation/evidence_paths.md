# FIG-P05 evidence paths

## 고정 입력과 기존 결과

- Project: `components/digital_accelerator/vivado_project/SNN_ECG_MB_FULL_REPLAY/SNN_ECG_MB_FULL_REPLAY.xpr`
- Block Design Tcl: `components/digital_accelerator/results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_bd.tcl`
- Rebuild Tcl: `components/digital_accelerator/results/board_replay/microblaze_full_replay/build_microblaze_full_replay_system.tcl`
- IP repositories: `components/digital_accelerator/ip_repo/`
- Board constraints: `components/digital_accelerator/constraints/nexys_a7_microblaze_full_replay.xdc`
- Fixed bitstream: `components/digital_accelerator/results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`
  - SHA256 `61dfb3dddee1f55b9e2ce42009cb9693bb1c8ff9c7b65b71f0d59d6b2a34dd58`
- Fixed XSA: `components/digital_accelerator/results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa`
  - SHA256 `8ff2a1ed537c27bd6d8117313c274aa79de8f11b4e6df54fa1b9fa10ca5942a3`
- Fixed system timing: `components/digital_accelerator/results/board_replay/microblaze_full_replay/reports/system_timing_summary.rpt`
  - SHA256 `7607366a0611ac73864ca6b84308f3e36f335d55591526d340ccb61a6deaeb12`
- Fixed hierarchical utilization: `components/digital_accelerator/results/board_replay/microblaze_full_replay/reports/system_utilization_hier.rpt`
  - SHA256 `659ff69b2937020ee6649001156dc9c8f70a1e46e88d5e58adbacf9e69104107`
- Fixed pure RTL metrics: `components/digital_accelerator/reports/final/final_metrics.json`
  - SHA256 `c5b2ea036d8814791b952c8e4f2ceeaef759f5f56e1af44fdfcc8bce651a3352`

## 재생성과 publication export

- `export_vivado_figures.tcl`: 동일 part, IP, BD, constraints와 기존 run strategy로 새 작업 project를 만들고 bitstream까지 구현한 뒤 routed checkpoint, timing, hierarchy와 worst path를 추출한다.
- 재생성 작업 디렉터리: `C:/Users/YangGeon/_ecg_p05_vivado_work/` (Git 비추적 임시 경로)
- `capture_vivado_device_views.ps1`: routed checkpoint를 Vivado GUI에서 열고 실제 Device/Schematic View 창을 PNG로 캡처한다.
- `build_publication_composite.py`: Vivado export의 방향·여백을 정리하고 실제 Device View를 crop하며 CSV와 SVG/PDF composite를 생성한다. 배치나 timing path를 새로 그리지 않는다.
- 재생성 원본: `timing_summary.rpt`, `hierarchical_utilization.rpt`, `worst_setup_path.rpt`, `worst_setup_path_metadata.csv`
- publication 원본: `device_view_full.png`, `device_view_accelerator_zoom.png`, `microblaze_block_design.png`, `worst_setup_path.png`
- publication 결과: `vivado_implementation_composite.svg`, `vivado_implementation_composite.pdf`

## 범위 경계

- `pure RTL WNS 8.184 ns`는 고정 standalone pure RTL 구현 범위다.
- `MicroBlaze system WNS 0.097 ns`와 worst setup path는 processor·interconnect·memory·UART·sample feeder·accelerator를 포함한 통합 system 범위다.
- Device View는 FPGA placement/routing이며 ASIC layout이 아니다.
- 물리 AFE PCB, ADC silicon, fabricated ASIC, ASIC post-layout 또는 clinical validation 근거로 사용하지 않는다.

