# MATLAB–LTspice nominal 비교 해석

## 확인된 사실

- MATLAB source는 fixed commit `907f7e1f081a9d6a5703a32095d962143315a192`의 함수들을 실행했다.
- 두 결과의 sample count는 각각 10,000이다.
- fixed MATLAB output은 0 s에서 시작하고 XMODEL-aligned LTspice direct aperture는 1.000 ms에서 시작한다.
- index-aligned 정착 후 MAE는 0.678 LSB, RMS error는 2.22460982846 LSB, correlation은 0.998591395027이다.
- 정착 후 best-lag diagnostic은 0 samples이며 zero-lag 결과를 대체하지 않는다.

## 해석과 한계

MATLAB은 digital HPF/notch/LPF 수식 모델이고 LTspice는 continuous-time R/C와 analog Twin-T를 사용한다. 따라서 bit-exact 일치는 요구하지 않으며, 이 비교는 nominal intent의 polarity, range, sampling 및 gross waveform consistency 진단으로 제한한다. 최종 LTspice 상관 gate의 기준은 MATLAB이 아니라 fixed XMODEL이다.
