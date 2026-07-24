# 검증 범위와 한계

- Physical AFE PCB나 bench 측정이 아니다.
- Fabricated ADC/SoC 또는 analog silicon 검증이 아니다.
- ADC는 behavioral limiter/floor quantizer이며 transistor-level SAR ADC가 아니다.
- Transistor-level, extracted parasitic 또는 post-layout 결과가 아니다.
- 실제 electrode, live subject, clinical 또는 regulatory validation이 아니다.
- Patient #100의 10초 예시는 population 전체 또는 장시간 동작 보증이 아니다.
- Nominal과 stress evidence는 별도 table/raw/log로 관리한다.
- ±5 V/UniversalOpamp2 결과는 `pre_alignment`이며 최종 claim에 사용하지 않는다.
- Fixed MATLAB digital filters와 LTspice analog Twin-T는 bit-exact 비교 대상이 아니다.
- Fixed XMODEL source contract 정합과 실제 code-stream equivalence는 다르다. 후자는 simulator 부재로 `PENDING_XMODEL_EXECUTION`이다.
- LTspice analog correctness는 locked XMODEL/RTL/FPGA equivalence, `final_pred/final_mem`, 4-class accuracy를 증명하지 않는다.
- ADC noise, jitter, 30분 regression과 locked RTL 영향은 XMODEL/RTL 소유 범위다.
