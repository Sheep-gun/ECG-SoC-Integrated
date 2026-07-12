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
- Fixed hierarchical utilization: `components/digital_accelerator/results/board_replay/microblaze_full_replay/reports/system_utilization_hier.rpt`
- Fixed pure RTL metrics: `components/digital_accelerator/reports/final/final_metrics.json`

## Vivado native vector exports

- `microblaze_block_design_vivado_native.pdf/.svg`
  - Vivado 2020.2 `write_bd_layout -format pdf/svg -scope all` 직접 출력
- `worst_setup_path_vivado_native.pdf/.svg`
  - Vivado 2020.2 `write_schematic -format pdf/svg -scope all` 직접 출력
- `native_vector_export.txt`
  - 실행한 export 형식과 Device View export 제한 기록

## Device 배치 데이터

- `placed_tile_occupancy.csv`
  - routed checkpoint의 tile `GRID_POINT_X/Y`별 primitive cell 수를 기록
  - `accelerator_core`와 `system_other` 범위를 분리
- `device_placement_map.svg/.pdf`
  - `placed_cells.csv`만으로 생성한 벡터 배치 분포
  - Vivado Device View 스크린샷 또는 GUI 화면 재현이 아님

## Publication 산출물

- `microblaze_block_design.pdf/.svg`: native vector에서 회전·여백만 정규화
- `worst_setup_path.pdf/.svg`: native vector에서 회전·여백만 정규화
- `vivado_implementation_composite.pdf`: placement map + 두 native vector의 3페이지 package
- `vivado_implementation_composite.svg`: screenshot-free routed placement overview
- `build_vector_publication.py`: rasterization 없이 위 산출물을 재생성

## 범위 경계

- `pure RTL WNS 8.184 ns`는 standalone pure RTL 구현 범위다.
- `MicroBlaze system WNS 0.097 ns`와 worst setup path는 processor·interconnect·memory·UART·표본 공급기·accelerator를 포함한 통합 system 범위다.
- 물리 AFE PCB, ADC silicon, fabricated ASIC, ASIC post-layout 또는 clinical validation 근거로 사용하지 않는다.
