# (debug/재현성 note — 공식 결과 아님) fast harness cadence와 case84

> 이 문서는 **디버깅/재현성 이력**이며 최종 claim에 사용하지 않는다.
> 공식 결과는 canonical board-facing cadence(`sample_gap_cycles=2`) 기준의
> `afe_locked_rtl_integration_36case_compare.csv/.md` 만 사용한다.

## 요지
- 초기 fast harness는 `sample_gap_cycles=0`(cycles 3.60M/case)로 36-case를 돌렸고, 이때 case 84(CHF chf06 w019) 1건만 final_membrane이 1표차(ARR 10→9, AFF 32→33)였다. final_pred(AFF)는 동일.
- 원인은 **XSim sample-input cadence 차이**(golden = gap=2, cycles 5.40M)이며 AFE waveform과 무관(입력 chunk는 SHA256 36/36 identical).
- **canonical cadence(`sample_gap_cycles=2`)에서 case 84 = 골든과 동일한 final_mem(1/-3/10/32), 전체 36/36 bit-exact로 해소**됨.
- `sample_gap_cycles=1`은 DUT의 sample_ready 주기(2 cycle)에 흡수되어 gap=0과 동일 결과 → gap=2가 board-facing golden cadence.

## 결론
전체 RTL이 임의 cadence에 invariant하다고 일반화하지 않으며, 공식 통합 결과는 digital golden과 동일한 canonical cadence 기준만 사용한다.
