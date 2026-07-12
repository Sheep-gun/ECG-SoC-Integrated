# SNN ECG Accelerator Benefit

## 범위

고정 SNN ECG 네 클래스 IP의 실행 이점을 모델 변경 없이 정량화하였다. 물리 보드 지연시간과 전력은 측정하지 않은 `NO_BOARD` benchmark다.

## 정확성 선행 조건

동일한 36개 1,800,000-sample stream을 사용했다. Exact C++는 최종 예측 36/36, 네 최종 막전위 144/144와 Snapshot 경계 1,080/1,080이 고정 RTL과 일치한 뒤에만 시간을 측정하였다. 분류 지표 29/36과 16/19, 고정 모델과 RTL은 변경하지 않았다.

## CPU와 RTL 결과

단일 스레드 transaction-level Exact C++의 360-run kernel 중앙값은 1,777.699800 ms이고 end-to-end 중앙값은 2,007.549250 ms다. Pure RTL은 `sample_gap_cycles=2`, 100 MHz와 profile cycle 5,401,260을 사용했으며, 저장된 30분 ECG 처리 지연시간은 54.012600 ms다. 처리량은 33.325557 MSamples/s이고 1 kSPS 입력 대비 처리 여유는 33,325.56배다.

동일한 kernel 처리 범위에서 `1777.699800 / 54.012600 = 32.912687`이다. 이 값은 측정 CPU와 cycle-derived FPGA accelerator-core를 결합한 **speedup estimate**이며 측정 보드 speedup이 아니다.

## live ECG와 저장 데이터 처리의 차이

54.012600 ms는 이미 저장된 1,800,000개 표본을 코어에 공급했을 때의 active processing time이다. 실제 1 kSPS ECG에서는 30분 분량의 표본이 들어오는 데 30분이 필요하므로 최종 판정의 관찰 지연시간이 54 ms로 줄어드는 것은 아니다.

## 자원·전력·에너지

Pure RTL은 LUT 9,719, FF 5,038, BRAM 0, DSP 0이다. 0.099 W는 Vivado 추정 전력이다. 이를 cycle-derived 처리 지연시간과 곱한 0.005347247400 J/decision도 추정값이며 물리 보드 측정값이 아니다.

## 남은 측정

보드 accelerator-core timing, MicroBlaze system timing, host-to-board latency, 물리 전력과 에너지는 모두 `PENDING_BOARD`다.
