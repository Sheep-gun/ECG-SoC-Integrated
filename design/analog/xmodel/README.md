# AFE–ADC XMODEL

이 디렉터리는 공개 digitized ECG를 PWL 전압 자극으로 재구성하고 AFE–ADC 동작을 SystemVerilog XMODEL로 재현하는 원본 설계와 검증 자산을 보관한다.

- 출력 규약: 1 kSPS signed 12-bit ECG stream
- 공칭 대역: 약 0.5–150 Hz
- 60 Hz Active Twin-T notch 포함
- LTspice–XMODEL 10초 비교: MAE 0.6445 LSB, 상관계수 0.999518, 지연 0표본
- AFE–RTL 직접 통합 검증: 36개 compact acceptance와 4개 보존 raw mixed-simulation dump를 구분해 보관

공개 문서에서는 `AF`를 사용한다. 원시 자산과 legacy 파일명의 `AFF`는 동일 클래스를 뜻한다. 물리 AFE PCB, ADC silicon과 임상 검증은 수행하지 않았다.
