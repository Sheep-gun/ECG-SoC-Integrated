# ECG AFE — XModel + Questa 통합 검증 보고서

> 제27회 대한민국 반도체설계대전 · 한양대학교 융합전자공학부
> 담당: 이수환 (아날로그 설계 + 통합 검증) · 작성일: 2026-06-21

## 1. 검증 환경

| 항목 | 내용 |
|---|---|
| 시뮬레이터 | Questa Intel Starter FPGA Edition 2024.3 |
| 아날로그 모델 | XModel 2025.12 (Scientific Analog), PLI `xmodel_msim` |
| 라이선스 | Questa node-lock(LR-164468) + XModel floating(9524@52.79.127.207) |
| OS | WSL2 Ubuntu (mirrored networking) |

**환경 구축 시 해결한 차단요소**
1. **타임스케일**: 설계/TB는 `timescale 1ns/1ns`이나 XModel 기본 `XMODEL_TIMEPRECISION=1ps` → 런타임 abort. 컴파일에 `+define+XMODEL_TIMEPRECISION=1ns` 추가로 해결.
2. **라이선스 hostid 충돌**: Questa는 MAC `00:15:5d:84:ee:1a` 필요. eth0 MAC 변경 시 네트워크가 끊겨 원격 XModel 라이선스 불가. FlexLM이 `eth0`/`loopback0`만 hostid로 읽는 점을 이용, **loopback0의 MAC만 라이선스 값으로 설정**(인터넷=eth0 유지). `qsim-license-nic.service`(systemd)로 부팅 자동화.
3. **vsim top**: `tb_* XMODEL_global` 둘 다 지정 + `-sv_lib/-pli xmodel_msim` 필수.

## 2. 설계 버그 수정 (Bug #10 ~ #15)

| # | 증상 | 원인 | 수정 |
|---|---|---|---|
| 10 | ADC 출력 고정(1939) | `x_opamp` 이산 relaxation이 3-opamp IA 피드백에서 차동모드 미수렴(이득 0) | XModel `vcvs` 솔버 모델로 교체 → 폐루프 이득 ×201 실현 |
| 11 | 실효이득 36 | Twin-T 노치 출력(~26kΩ)을 1kΩ LPF가 로딩 | 노치 출력 버퍼 삽입 |
| 12 | LPF 159Hz > 150Hz | C=1µF | C=1.06µF (150Hz) |
| 13 | CMRR 경계(=100dB) | opamp CMRR 100dB | 110dB 마진 |
| 14 | ADC 로그 off-by-one | NBA 갱신 전 읽기 | `$fstrobe` + fd 수명 정리 |
| 15 | 대역폭 17Hz (150Hz 스펙 미달) | 수동 Twin-T 저-Q 광대역 감쇠 | 능동 Twin-T (부트스트랩 k=0.95, Q≈5) |

## 3. 측정 결과 (정량 검증)

**주파수 응답** (`make char`, tb_afe_char.sv)

| f(Hz) | 수동노치 이득 | 능동노치 이득 |
|---|---|---|
| 10 | 165 | 199.8 |
| 20 | 110 | 198.2 |
| 40 | 39.5 | 188.5 |
| 60 | 0.015 (노치) | 0.019 (노치) |
| 150 | 65.9 | 141 (−3dB) |

- 통과대역 ~200 (이상 201의 99%), **−3dB 대역폭 150Hz** (수동: 17Hz)
- **60Hz 노치 80dB**, CMRR 156dB (모델; 실제는 저항매칭 제한)

**60Hz PLI 제거** (`make pli`, tb_ecg_pli.sv)

| 주입 | ECG 잔차(284mV 신호 대비) |
|---|---|
| 공통모드 0.5V + 차동 1mV | RMS 0.92 mV (0.3%) |
| 공통모드 1V + 차동 2mV (극한) | RMS 0.91 mV (0.3%) |

→ CMRR와 능동 노치가 실전 결합 간섭을 완전히 제거.

**ECG 복원** (`make sim`, real_ecg_100.pwl, MIT-BIH Record 100=NSR)
- 5000 샘플, ADC 진폭 284mV p-p (코드 1980~2333)
- R-peak 검출, R-R ≈ 790ms (~76 bpm, 규칙적 NSR) — 정상

## 4. 스펙 충족 (IEC 60601-2-47)

| 항목 | 목표 | 측정 | |
|---|---|---|---|
| IA 이득 | 201 | ~200 | ✅ |
| HPF | ≤0.67Hz | 0.48Hz | ✅ |
| −3dB 대역폭 | 150Hz | 150Hz | ✅ |
| 60Hz 노치 | 제거 | 80dB | ✅ |
| CMRR | >100dB | 156dB* | ✅ |
| ADC/샘플링/공급 | 12b/1kSPS/±1.65V | 동일 | ✅ |

*저항 이상매칭 가정. 실제는 매칭 오차로 제한(0.1%→~66dB) — 정밀저항/트리밍 필요.

## 5. 재현 방법

```bash
cd ~/ECG-SoC
make sim     # ECG 시뮬 (~25s)
make char    # 주파수 응답/CMRR
make pli     # 60Hz 간섭 제거
make vcd     # 짧은 구간 + VCD 파형
```

원본 백업: `analog/ecg_afe_xmodel.sv.bak`(최초 relaxation), `.prenotch`(능동노치 이전).
