# AFE–ADC XMODEL과 고정 Pure RTL 직접 통합

이 디렉터리는 AFE–ADC XMODEL 출력과 고정 Pure RTL 코어를 중간 파일 없이 연결하는 통합 testbench의 표준 위치다.

- `tb_snn_ecg_30min_mixed_e2e.sv`: offset-binary ADC 출력의 signed 12-bit 변환, `sample_valid` 생성, RTL 입력 handoff와 최종 결과 기록
- `sources_questa.f`: 직접 통합에 필요한 RTL module 목록

RTL 원본은 이 디렉터리에 복제하지 않는다. 모든 digital source authority는 `design/digital/rtl/`이며 고정 commit은 `c6b80de19cdcad5b7e43fe7835588b629d847f75`다.

전체 직접 통합을 다시 실행하려면 원본 WFDB/PWL 자료, XMODEL 2025.12 및 지원되는 Questa 라이선스 환경이 필요하다. 고정 XMODEL commit은 `4756a5086023547328ef44fd5fd87da3c250dc39`다.
