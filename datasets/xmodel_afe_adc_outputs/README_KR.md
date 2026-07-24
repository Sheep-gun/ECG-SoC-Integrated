# XMODEL AFE–ADC 출력 데이터

이 디렉터리는 고정 AFE–ADC XMODEL이 생성하고 직접 통합된 RTL 코어가 수락한 30분 signed 12-bit ADC 출력의 표준 보관 위치다.

## 현재 보유 범위

- `representative_4case/`: NSR, CHF, ARR, AF 각 1개씩 총 4개 실제 XMODEL 출력
- 파일당 1,800,000표본, 1 kSPS, 한 줄당 12-bit 3자리 hexadecimal two's-complement code
- `case_manifest_36case.txt`: 전체 잠금 시험 36개 case 목록

현재 로컬 및 저장소에서 확인된 실제 full-30분 XMODEL 출력은 **4/36개**다. 나머지 32개는 원본 WFDB에서 PWL을 생성하고 라이선스가 있는 XMODEL/Questa 환경에서 다시 실행해야 한다. 누락 case를 Python emulator 출력으로 대체하지 않는다.

## 재현과 검증

다음 스크립트가 보유한 4개 입력을 고정 Pure RTL에 재생하고, 입력 SHA-256, 30개 Snapshot, 최종 클래스와 네 Final Membrane을 직접 통합 결과와 비교한다.

```text
tools/verification/run_xmodel_adc_pure_rtl_replay.py
```

검증 결과와 직접 통합 로그는 `verification/xmodel_rtl_e2e/`에 있다. 36개 전체 XMODEL 출력이 존재하지 않으므로 저장소의 재실행 결과는 의도적으로 4개 PASS와 32개 `MISSING_XMODEL_ADC`를 구분한다.
