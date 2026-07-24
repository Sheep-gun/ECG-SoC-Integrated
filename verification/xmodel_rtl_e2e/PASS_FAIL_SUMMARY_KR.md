# 실제 XMODEL ADC → 고정 Pure RTL XSim replay 검증

## 판정: **FAIL (완전한 36-case 검증 불가)**

고정 RTL은 commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`, top `snn_ecg_30min_final_top`이다. source-of-truth manifest의 고정 커밋 SHA와 실제 사용 RTL 17개 파일이 모두 일치했다.

실제 XMODEL accepted ADC dump가 있는 **4개**는 모두 1,800,000표본, signed 12-bit 형식이며 새 Vivado 2020.2 XSim replay에서 직접 통합 결과와 입력 SHA, 최종 클래스, 네 Final Membrane, 30 Snapshot, 1 final decision이 bit-exact했다. 그러나 나머지 **32개**의 실제 XMODEL full-30분 dump가 없어 전체 PASS 기준을 충족하지 못한다.

- 입력 SHA-256: 4/36
- 최종 클래스: 4/36
- Final Membrane: 16/144
- accepted samples: 4/36
- Snapshot: 4/36
- final decision: 4/36

`part1_input_sha256_compare_36case.csv`의 36/36은 emulator chunk와 기존 RTL replay 입력의 무결성 결과이며, 실제 XMODEL 36개 존재/동일성을 뜻하지 않는다. 누락분을 emulator 파일로 대체하지 않았다.
