# Digital SNN ECG accelerator

이 디렉터리는 고정 SNN 기반 Pure RTL, AXI IP, strict source-record-wise 평가 설정과 RTL/XSim/FPGA 원시 근거를 보관한다.

- 고정 Pure RTL commit: `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- 입력: 1 kSPS signed 12-bit ECG
- 출력: NSR, CHF, ARR, AF
- 60초 Snapshot 30개를 30분 Final Membrane에 누적
- 최종 시험: 29/36, 정확도 80.56%, Macro-F1 80.44%
- Pure RTL: 9,719 LUT, 5,038 FF, BRAM 0, DSP 0, WNS 8.184 ns

legacy 설정과 원시 파일의 `AFF` 표기는 공개 문서의 `AF` 클래스와 같다. 통합 설명은 `docs/DIGITAL_ARCHITECTURE_KR.md`, 검증 범위는 `docs/INTEGRATION_VERIFICATION_KR.md`, 최종 수치는 `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`를 기준으로 한다.
