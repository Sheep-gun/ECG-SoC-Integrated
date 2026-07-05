# Judge Q&A Defense

## Q1. 원본 ECG가 이미 디지털인데 AFE+ADC를 다시 거치는 이유는?

true raw analog recovery가 아니다. 공개 ECG dataset은 이미 digitized record이므로, 본 프로젝트는 그 sample을 physical-voltage-equivalent `vin_v`로 재구성하고 virtual DAC/PWL-equivalent replay로 AFE+ADC XMODEL 입력을 만든다. 이후 HPF, gain, 60 Hz notch, LPF, 12-bit ADC quantization을 적용해 RTL이 받는 signed 12-bit stream을 만든다.

## Q2. record-wise split인가?


## Q3. 임상적으로 유효한 진단기인가?

아니다. 본 프로젝트는 clinical validation이 아니라 FPGA/VLSI engineering prototype이다. 목표는 ECG classification workload를 streaming RTL accelerator IP로 구현하고 검증하는 것이다.

## Q4. 왜 Accelerator IP Core인가?

ECG stream 처리, event/spike extraction, class membrane accumulation, final WTA decision을 전용 RTL datapath로 구현했다. AXI wrapper, IP-XACT `component.xml`, xgui, sample feeder, MicroBlaze smoke system이 있어 reusable IP block 관점의 evidence가 있다.

## Q5. 이화여대 작품처럼 analog IC 검증이 있나?

아니다. 이화여대 계열 강점은 Virtuoso/layout/post-layout 및 biomedical CMOS system이다. 본 프로젝트는 AFE+ADC XMODEL/nominal behavior와 digital IP 검증 중심이다. analog physical design은 향후 보완 항목이다.

## Q6. UNIST GNN accelerator와 비교하면 약한 점은?

workload scale, HBM, 대형 accelerator optimization, 엄격한 baseline speedup/energy claim은 UNIST 유형이 더 강하다. 본 프로젝트의 차별점은 low-resource biomedical streaming accelerator이며, DSP/BRAM 0 core, ECG-specific event logic, AXI/IP packaging이 강점이다.

## Q7. 실제 board에서 돌렸나?

현재 evidence는 bitstream programming, MicroBlaze smoke bit/XSA, XSDB MMIO smoke, Vitis-built ELF, UART bare-metal PASS transcript, 그리고 test NSR case 0 full-record board replay PASS transcript 수준이다. 전체 test split board replay나 physical AFE/ADC replay는 아직 TODO이다. 없는 것을 완료됐다고 말하지 않는다.

## Q8. 88.89%가 최종 성능인가?
