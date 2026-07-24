# Vivado 원본 구현 근거

이 디렉터리는 사용자 홈에 분산되어 있던 Vivado 2020.2 임시 프로젝트를 제거하기 전에 보존한 최소 원본 산출물이다. 생성 캐시와 IP별 중간 checkpoint는 제외하고, 보고서 Figure와 구현 수치를 다시 확인하는 데 필요한 routed checkpoint 및 핵심 report만 유지한다.

## 디렉터리 구성

- `post_route_device/`
  - 보고서의 post-route Device View와 계층별 배치 분석에 사용한 고정 `system_routed.dcp`
  - 해당 구현의 timing, utilization, power, route status 및 DRC report
- `system_power/`
  - MicroBlaze 통합 시스템의 전력 분석 실행에서 보존한 routed checkpoint
  - 해당 실행의 power, timing, utilization, route status 및 DRC report

두 checkpoint는 과거 disposable project의 생성물이며 새로운 정식 Vivado project가 아니다. 재구성 가능한 정식 project는 다음 두 개만 유지한다.

- Pure RTL: `vivado/pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr`
- MicroBlaze 통합: `vivado/microblaze/SNN_ECG_MB_FULL_REPLAY.xpr`

## 사용 범위

`post_route_device/system_routed.dcp`는 `verification/fpga_implementation/extract_hierarchy_placement.tcl`과 Figure export script에서 직접 열 수 있다. 모든 파일의 크기와 SHA-256은 `sha256_manifest.csv`에 기록하였다.

`system_power/power_routed.rpt`는 Vivado 추정 보고서이며 물리 보드 실측값이 아니다. 이 report의 Total On-Chip Power는 0.271 W, Dynamic은 0.173 W, Device Static은 0.098 W이고 confidence level은 Medium이다. 가속기 할당전력, 판정당 에너지 또는 이상적 power-gating 평균전력과 혼동해서는 안 된다.
