# Ablation Study

## 1. 최종 제출 기준

현재 최종 모델은 `structural_guarded_silent_aff_1008710` locked Final Membrane이며, 성능 주장은 strict record-wise train/validation-only lock과 final_test 1회 평가 결과만 사용한다.

기존 chunk feature dump 기반 ablation benchmark는 최종 locked 모델의 주장 근거로 사용하지 않는다. 따라서 README/FINAL_REPORT의 핵심 결과 표에는 포함하지 않고, 최종 제출 기준에서는 retired legacy analysis로만 취급한다.

## 2. 주장 가능한 범위

| 항목 | 최종 상태 |
|---|---|
| Snapshot 모델 | 고정된 60초 Snapshot Readout |
| Final Membrane | strict record-wise train/validation만으로 lock |
| Final test | lock 이후 1회 평가 |
| 최종 성능 주장 | final_test 29/36 = 80.56%, record-majority 16/19 = 84.21% |
| final_test 재튜닝 | 수행하지 않음 |

## 3. 남은 ablation TODO

아래 항목은 최종 locked 모델 기준으로 새로 재생성해야 하며, 현재 최종 성능 근거로 주장하지 않는다.

| TODO | 이유 |
|---|---|
| Snapshot-only vs locked Final Membrane | locked split 기준으로 다시 계산 필요 |
| AFE-off full-record `.mem` | raw-converted non-AFE dataset 재생성 필요 |
| HPF/notch/LPF-off `.mem` | AFE/XMODEL conversion pipeline variant 필요 |
| RTL feature module synthesis ablation | 별도 RTL variant와 synthesis run 필요 |

## 4. 방어 문장

최종 제출 문서에서는 ablation을 “완료된 최종 수치”로 주장하지 않는다. 본 프로젝트의 최종 검증 축은 locked strict record-wise protocol, Python/XSim bit-accurate check, Vivado/IP packaging, Vitis/MicroBlaze class-wise board replay이다.
