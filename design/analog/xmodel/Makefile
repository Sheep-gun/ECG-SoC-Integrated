# ================================================================
#  제27회 대한민국 반도체설계대전 — ECG AFE Mixed-Signal Simulation
#  Makefile  (버전 v4.0 — 검증된 스크립트 플로우로 위임)
#
#  핵심 수정(2026-06-21 통합검증):
#   - vlog 컴파일에 +define+XMODEL_TIMEPRECISION=1ns (1ps↔1ns 충돌 해결)
#   - vsim top에 XMODEL_global 포함, -sv_lib/-pli xmodel_msim
#   - Questa 라이선스 hostid는 qsim-license-nic.service가 loopback0에 설정(부팅 자동)
#  실제 컴파일/시뮬 로직은 scripts/ 에 있음(라이선스 env·경로 일원화).
#
#  사용법:
#    make sim     → ECG 시뮬 (전체 5초, VCD off, ADC 로그)
#    make vcd     → 짧은 구간(300ms) + 전계층 VCD (파형 관찰)
#    make char    → 주파수 응답 + CMRR 특성 측정
#    make pli     → 60Hz 전원선 간섭 제거 검증
#    make clean   → 생성물 삭제
# ================================================================
.PHONY: sim vcd char pli clean

sim:
	bash scripts/run_afe_sim.sh

vcd:
	bash scripts/run_afe_sim.sh vcd 300ms

char:
	bash scripts/run_char.sh

pli:
	bash scripts/run_pli.sh

clean:
	rm -rf sim_out real_ecg_100.pwl transcript vsim.wlf
	@echo "  clean 완료"
