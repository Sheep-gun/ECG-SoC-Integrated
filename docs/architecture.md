# RTL Architecture

## 전체 경로

~~~text
ECG adc_data stream
-> event encoder
-> QRS LIF detector
-> feature spike generation
-> local class neuron membrane
-> segment-level class membrane
-> RBBB/EERG readout
-> WTA
-> pred_class
~~~

## Local / Segment Membrane

60초 local window 동안 feature spike가 class neuron membrane에 직접 누적됩니다. window가 끝나면 local membrane 값을 segment-level membrane에 누적하고 local membrane은 초기화합니다.

이 방식은 긴 segment에서 단순 count가 계속 커지는 문제를 줄이고, 60초 단위 evidence를 안정적으로 모으기 위한 구조입니다.

## WTA

segment_done 시점에서 NSR, CHF, ARR, AFF class membrane 중 가장 큰 값을 갖는 class가 winner가 됩니다. 이 비교기는 SNN class neuron의 readout이며 STDP 학습이 아닙니다.

## 구현 원칙

- fixed signed synaptic weight
- counter, comparator, shift/add 중심 구현
- floating point 없음
- DSP multiplier 없음
- backpropagation/STDP 없음
