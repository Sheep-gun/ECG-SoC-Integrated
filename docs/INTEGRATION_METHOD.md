# Integration method

통합 경계는 `1 kSPS signed 12-bit two's-complement ECG + sample_valid`다.

1. 공개 ECG를 PWL 전압 자극으로 재구성한다.
2. MATLAB과 LTspice에서 AFE–S/H–ADC 특성을 확인한다.
3. SystemVerilog XMODEL이 `adc_signed[11:0]`과 `sample_valid`를 생성한다.
4. 고정 Pure RTL 코어가 중간 파일 없이 해당 신호를 받아 60초 Snapshot 30개와 최종 판정을 생성한다.
5. 별도 AXI IP는 AXI-Lite 제어와 AXI-Stream 입력으로 패키징하고 MicroBlaze FPGA에서 재생한다.

AFE–RTL direct integration과 AXI/MicroBlaze integration은 서로 다른 검증 범위다. 전자는 동일 XMODEL 환경의 signal handoff와 최종 출력 정합을, 후자는 FPGA 제어 및 데이터 공급 경로를 검증한다.
