# XMODEL-Aligned LTspice AFE+ADC Validation

이 폴더는 ECG AFE+ADC의 **XMODEL 정렬 LTspice 검증 사본**이다. 기존 ±5 V 회로는 최종 근거로 사용하지 않으며, 여기에는 ±1.65 V XMODEL 기준으로 다시 구성하고 실행한 최종 후보만 포함한다.

## 현재 상태

| 단계 | 상태 | 의미 |
|---|---|---|
| MATLAB nominal pre-validation | 완료 | 필터·이득·ADC 범위의 사전 의도 검증 |
| LTspice schematic 및 검증 | 완료 | 실제 ASC/netlist에서 AC, 10초 ECG, S/H, ADC mapping, mismatch, GBW, VOS, PLI 실행 |
| LTspice 내부 direct/S&H 비교 | 완료 | 두 스트림을 분리해 10,000 sample 비교 |
| XMODEL 대 LTspice 직접 상관 | 완료 | 동일 10초 ECG 10,000 sample, MAE 0.6445 LSB, correlation 0.999518, lag 0 |

따라서 현재 결과는 **MATLAB design reference -> XMODEL-aligned LTspice schematic -> SystemVerilog XMODEL**의 단계별 model-based validation evidence다. XMODEL-LTspice 비교는 bit-exact가 아니라 ±5/±10 LSB coverage와 correlation으로 해석한다. 보고서 본문과 handoff figure는 [`../../docs/MIXED_SIGNAL_VERIFICATION_KR.md`](../../docs/MIXED_SIGNAL_VERIFICATION_KR.md)에 정리했다.

공개 저장소 반입 과정에서 LTspice가 자동 기록한 개인 홈 디렉터리 접두사는 `<USER_HOME>`으로 비식별화했다. 회로 값, 측정값, 명령 인자, run status와 SHA-256은 유지한다.

## LTspice에서 완료된 일

- U1~U6 전원: ±1.65 V
- Aol 100 dB, CMRR 110 dB, Rout 1 Ω, nominal GBW 1 GHz, VOS 0의 전용 op-amp abstraction
- ECG+=patient, ECG−=0 V, 50 µs ZOH input update
- direct ADC aperture: 1.000 ms부터 1 kSPS
- LTspice 전용 S/H: 각 1 ms period의 0.9~1.0 ms 부근 track
- 12-bit ADC limiter/floor/signed mapping 검증
- AC, nominal transient, S/H, ADC mapping, timestep convergence, DC/baseline/PLI/mismatch/GBW/VOS stress 총 35개 run
- 35개 run 모두 `EXECUTED`, fatal/warning signature 0건
- direct 및 S/H vector 각각 10,000 sample, endpoint clipping 0건

주요 nominal 결과는 HPF 0.481 Hz, IA 200.594 V/V, 60 Hz notch −83.56 dB, LPF 150.211 Hz이다. 정착 후 AFE 출력은 −0.0540~+0.2466 V이며 ADC rail 최소 여유는 1.403 V이다.

## XMODEL-LTspice 상관 결과

| Error band / metric | 결과 |
|---|---:|
| Exact | 56.49% |
| ±5 LSB | 98.74% |
| ±10 LSB | 99.89% |
| Mean / MAE | +0.0221 / 0.6445 LSB |
| RMS / maximum | 1.3020 / 13 LSB |
| Correlation / lag | 0.999518 / 0 sample |
| Clipping | 0 |

10,000개 중 11개만 ±10 LSB를 초과했고 잔여 오차는 급격한 QRS edge의 input-grid/sub-sample solver timing 부근에 집중됐다. 보고서에서는 ±5 LSB를 nominal agreement band, ±10 LSB를 extended QRS-edge band로 사용한다.

시스템/FPGA 대회에서 행동·회로 수준 AFE 근거로 필요한 핵심 단계는 완료됐다. 실제 아날로그 IC 또는 PCB 성능을 주장하려면 별도로 실제 부품/트랜지스터 모델, PVT·Monte Carlo, noise, THD, power 및 필요 시 post-layout/실측 검증이 필요하다.

## 주요 파일

- `schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc`: 최종 graphical schematic
- `schematics/xmodel_aligned/XOpAmp_XMODEL.lib`: XMODEL 정렬 op-amp abstraction
- `schematics/xmodel_aligned/patient100_xmodel_drive_10s.txt`: 최종 schematic 입력
- `results/xmodel_aligned/nominal/ltspice_xmodel_aligned_adc_samples.csv`: 10,000 sample 결과
- `results/xmodel_aligned/nominal/ltspice_xmodel_aligned_direct_adc_signed.mem`: LTspice direct-aperture 후보
- `results/xmodel_aligned/nominal/ltspice_track_hold_adc_signed.mem`: LTspice S/H vector
- `tables/xmodel_aligned_execution_manifest.csv`: 35개 실행 목록
- `tables/xmodel_ltspice_handoff_metrics.csv`: 후속 10초 XMODEL-LTspice 직접 상관 요약
- `report/report_update_draft_ko.md`: 보고서용 상세 결과
- `../../docs/MIXED_SIGNAL_VERIFICATION_KR.md`: 최신 MATLAB-LTspice-XMODEL 통합 서술과 최종 figure

약 13.87 GiB의 LTspice RAW는 Git에서 제외했다. 재실행용 회로·원본 입력·스크립트와 소형 log/command record는 포함되어 있다.

## 재실행

Windows PowerShell에서 LTspice 경로가 자동 탐색되지 않으면 명시적으로 전달한다.

```powershell
.\scripts\run_all.ps1 -SkipMatlab -Python python -Ltspice "C:\path\to\LTspice.exe"
```

MATLAB 비교 결과와 XMODEL SystemVerilog reference subset은 이 폴더에 보존했지만 각 원본 저장소 전체는 중복 복사하지 않았다. 이 폴더의 기존 `PENDING_XMODEL_EXECUTION` 표와 초안은 LTspice handoff 당시의 pre-run 상태를 보여주는 source snapshot이며, 최신 직접 상관 판정은 위 결과와 final analog report를 사용한다.
