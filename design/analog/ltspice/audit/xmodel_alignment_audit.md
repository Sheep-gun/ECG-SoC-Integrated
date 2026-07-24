# XMODEL 정합 LTspice schematic audit

## 근거 범위

- 원본 source of truth 감사 대상: `../FULL_AFE_ADC_SH.asc`
- 최종 validation copy: `schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc`
- LTspice 생성 netlist: `schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.net`
- 고정 XMODEL source: commit `4756a5086023547328ef44fd5fd87da3c250dc39`

원본 ASC는 수정하지 않았다. 원본의 `K_DIV`/positive rail node collision과 ±5 V
`UniversalOpamp2`는 `audit/schematic_audit.md`에 그대로 보존한다. 최종 결과는 아래
별도 copy에서만 생성하였다.

## 확인된 정합 항목

1. U1~U6 supply pin은 `VPLUS=+1.65 V`, `VMINUS=-1.65 V`이다. Bootstrap
   `K_DIV`는 supply와 분리되어 R15/R16의 0.95 divider로만 사용된다.
2. U1~U6은 `XOPAMP_XMODEL` subcircuit을 사용한다. Nominal parameter는
   Aol 100 dB, CMRR 110 dB, Rout 1 ohm, GBW 1 GHz, VOS 0이다.
3. VOS hook은 U1=+VOS, U2=-VOS에만 연결되고 U3~U6은 0이다. GBW hook은
   U1~U6 모두에 연결된다.
4. Nominal input은 `V3 INP_RAW 0 PWL ...`, `V5 INN_RAW 0 0`이다. Patient 값은
   고정 XMODEL testbench처럼 50 us update에 맞춘다.
5. HPF, IA, active Twin-T, bootstrap, LPF component 값은 고정 XMODEL topology와
   동일한 nominal 값이다. HPF/LPF/bootstrap에는 mismatch hook을 넣지 않았다.
6. S/H clock은 `PULSE(0 5 900u 1u 1u 98u 1m)`이다. Switch가 확실히 off인
   1.000 ms 직후를 S/H valid phase로 사용한다. XMODEL-equivalent direct ADC는
   매 1.000 ms falling-edge aperture의 `AFE_OUT`을 별도로 quantize한다.
7. ADC limiter, floor quantizer, endpoint 4095 scale, `ADC_CODE-2048` signed mapping은
   원본 및 XMODEL 계약과 동일하다. 이 블록은 behavioral voltage representation이며
   physical SAR ADC가 아니다.

## 남은 모델 차이

- XMODEL은 XMODEL primitive/solver를 사용하고 LTspice subcircuit은 B source,
  one-pole RC, `limit()`과 resistor로 동일 계약을 근사한다. 동일 source code가 아니다.
- S/H는 LTspice에만 있는 추가 구현이다. 따라서 direct stream과 S/H stream을 분리했다.
- Questa/XMODEL executable이 없어 fixed XMODEL code stream 자체는 실행하지 못했다.
  직접 상관 gate는 `PENDING_XMODEL_EXECUTION`이다.
- 이 감사와 실행은 schematic-level model-based evidence이며 PCB, fabricated IC,
  transistor-level SAR 또는 post-layout evidence가 아니다.
