#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; YLW='\033[1;33m'; GRN='\033[0;32m'
CYN='\033[0;36m'; BLD='\033[1m'; NC='\033[0m'
info()  { echo -e "${CYN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GRN}[ OK ]${NC}  $*"; }
err()   { echo -e "${RED}[ERR ]${NC}  $*"; }
step()  { echo -e "\n${BLD}${CYN}━━━ $* ━━━${NC}"; }
sep()   { echo -e "${CYN}================================================================${NC}"; }

sep
echo -e "${BLD}  ECG AFE XModel + Questa  v4.0${NC}"
sep

XMODEL_HOME="${XMODEL_HOME:-$HOME/xmodel_2025.12_x86_64}"
QUESTA_HOME="${QUESTA_HOME:-$HOME/intelFPGA/25.1/questa_fse/questa_fse}"
VLIB="${QUESTA_HOME}/bin/vlib"
VLOG="${QUESTA_HOME}/bin/vlog"
VSIM="${QUESTA_HOME}/bin/vsim"
XMODEL_PKG="${XMODEL_HOME}/include/xmodel_pkg.sv"
XMODEL_F="${XMODEL_HOME}/include/xmodel.f"
XMODEL_PLI="${XMODEL_HOME}/lib/x86_64/xmodel_msim.sl"
XMODEL_LIB="${XMODEL_HOME}/lib/x86_64/xmodel_msim"
DESIGN_SV="analog/ecg_afe_xmodel.sv"
TB_SV="tb/tb_ecg_afe.sv"
PWL_FILE="data/real_ecg_100.pwl"
SIM_OUT="sim_out"
WORK_LIB="${SIM_OUT}/work"
SIM_LOG="${SIM_OUT}/questa_sim.log"
TOP_MODULE="tb_ecg_afe"
VLOG_COMMON="-sv -mfcu +define+XMODEL +incdir+${XMODEL_HOME}/include -work ${WORK_LIB}"

source ~/.bashrc 2>/dev/null || true
export LD_LIBRARY_PATH="${XMODEL_HOME}/lib/x86_64:${LD_LIBRARY_PATH:-}"

step "STEP 1/5 : 환경 점검"
FAIL=0
[ -z "${SALMD_LICENSE_FILE:-}" ] && { err "SALMD_LICENSE_FILE 미설정"; FAIL=1; } || ok "SALMD_LICENSE_FILE OK"
[ -z "${LM_LICENSE_FILE:-}" ]    && { err "LM_LICENSE_FILE 미설정";    FAIL=1; } || ok "LM_LICENSE_FILE OK"
for F in "${XMODEL_PKG}" "${XMODEL_F}" "${XMODEL_PLI}"; do
    [ ! -f "${F}" ] && { err "파일 없음: ${F}"; FAIL=1; } || ok "$(basename ${F})"
done
for B in "${VLIB}" "${VLOG}" "${VSIM}"; do
    [ ! -x "${B}" ] && { err "실행파일 없음: ${B}"; FAIL=1; } || ok "$(basename ${B})"
done
for S in "${DESIGN_SV}" "${TB_SV}"; do
    [ ! -f "${S}" ] && { err "소스 없음: ${S}"; FAIL=1; } || ok "${S}"
done
[ ! -f "${PWL_FILE}" ] && echo -e "${YLW}[WARN]${NC}  PWL 없음: ${PWL_FILE}" || ok "${PWL_FILE}"
[ "${FAIL}" -eq 1 ] && { err "환경 점검 실패"; exit 1; }
ok "환경 점검 통과"

step "STEP 2/5 : 작업 디렉터리 준비"
mkdir -p "${SIM_OUT}"
> "${SIM_LOG}"
[ -d "${WORK_LIB}" ] && rm -rf "${WORK_LIB}"
"${VLIB}" "${WORK_LIB}" 2>&1 | tee -a "${SIM_LOG}"
ok "work 라이브러리 초기화"
[ -f "${PWL_FILE}" ] && [ ! -e "real_ecg_100.pwl" ] && \
    ln -sf "$(pwd)/${PWL_FILE}" real_ecg_100.pwl && ok "PWL 링크 생성"

step "STEP 3/5 : 컴파일"

echo ""; info "[1/4] XModel 패키지 (xmodel_pkg.sv) ..."
"${VLOG}" ${VLOG_COMMON} "${XMODEL_PKG}" 2>&1 | tee -a "${SIM_LOG}"
[ "${PIPESTATUS[0]}" -ne 0 ] && { err "xmodel_pkg 실패"; exit 1; }
ok "xmodel_pkg.sv 완료"

echo ""; info "[2/4] XModel 전체 primitive (-f xmodel.f) ..."
info "      resistor, capacitor, xreal_to_real, XMODEL_global 등 전체 포함"
"${VLOG}" ${VLOG_COMMON} -f "${XMODEL_F}" 2>&1 | tee -a "${SIM_LOG}"
[ "${PIPESTATUS[0]}" -ne 0 ] && { err "xmodel.f 실패"; exit 1; }
ok "xmodel.f 전체 완료"

echo ""; info "[3/4] 설계 파일 (ecg_afe_xmodel.sv) ..."
"${VLOG}" ${VLOG_COMMON} +acc "${DESIGN_SV}" 2>&1 | tee -a "${SIM_LOG}"
[ "${PIPESTATUS[0]}" -ne 0 ] && { err "설계 파일 실패"; exit 1; }
ok "ecg_afe_xmodel.sv 완료"

echo ""; info "[4/4] 테스트벤치 (tb_ecg_afe.sv) ..."
"${VLOG}" ${VLOG_COMMON} +acc "${TB_SV}" 2>&1 | tee -a "${SIM_LOG}"
[ "${PIPESTATUS[0]}" -ne 0 ] && { err "테스트벤치 실패"; exit 1; }
ok "tb_ecg_afe.sv 완료"
echo ""; ok "전체 컴파일 성공"

step "STEP 4/5 : 시뮬레이션 실행"
info "Top: ${TOP_MODULE} + XMODEL_global"
info "sv_lib: ${XMODEL_LIB}"
info "PLI   : ${XMODEL_PLI}"
echo ""

SIM_START=$(date +%s)
"${VSIM}" -c -t 1ns \
    -sv_lib "${XMODEL_LIB}" \
    -pli    "${XMODEL_PLI}" \
    -work   "${WORK_LIB}" \
    ${TOP_MODULE} XMODEL_global \
    -do "log -r /*; run -all; quit -f" \
    2>&1 | tee -a "${SIM_LOG}"

VSIM_RC="${PIPESTATUS[0]}"
SIM_ELAPSED=$(( $(date +%s) - SIM_START ))

if [ "${VSIM_RC}" -ne 0 ]; then
    err "vsim 실패 (exit=${VSIM_RC}, ${SIM_ELAPSED}초)"
    echo "  마지막 30줄:"; tail -30 "${SIM_LOG}" | sed 's/^/  /'
    exit 1
fi
ok "시뮬레이션 완료 (${SIM_ELAPSED}초)"
for F in ecg_result.vcd adc_output.txt; do
    [ -f "${F}" ] && mv "${F}" "${SIM_OUT}/" && ok "${F} → ${SIM_OUT}/"
done

step "STEP 5/5 : 결과 요약"
ADC_LOG="${SIM_OUT}/adc_output.txt"
if [ -f "${ADC_LOG}" ]; then
    printf "  총 샘플  : %d\n" "$(grep -v '^#' ${ADC_LOG} | wc -l)"
    printf "  유효 샘플: %d (t>=2s)\n" "$(grep -v '^#' ${ADC_LOG} | awk '$1>=2000' | wc -l)"
    grep -v "^#" "${ADC_LOG}" | awk '$1>=2000 {s+=$2;c++;
        if($2>mx||c==1)mx=$2;if($2<mn||c==1)mn=$2}
        END{if(c>0)printf "  전압 범위: %.4fV ~ %.4fV\n",(mn/4095)*3.3-1.65,(mx/4095)*3.3-1.65}'
fi
sep
echo "  ADC 로그 : ${SIM_OUT}/adc_output.txt"
echo "  VCD 파형 : ${SIM_OUT}/ecg_result.vcd"
sep
