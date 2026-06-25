# AFE and Mixed-Signal Integration

## 목적

아날로그 AFE 및 mixed-signal 검증 자료는 최종 RTL classifier가 실제 ECG acquisition chain과 연결될 때 필요한 입력 범위, sampling, ADC interface 조건을 정리하기 위한 자료입니다.

## 디지털 입력 가정

- sampling rate: 1 kSPS
- ADC format: signed 12-bit
- input stream: `adc_data`
- baseline-centered ECG waveform

## 연동 시 확인할 항목

- AFE 출력 swing이 12-bit signed range 안에 들어오는지
- baseline drift가 QRS, RAM, DSCR feature에 과도하게 영향을 주지 않는지
- ADC sampling clock과 RTL clock domain 연결 방식
- reset, segment_start, segment_done 제어 방식
- board demo ROM 입력과 실제 ADC stream 입력의 교체 위치
