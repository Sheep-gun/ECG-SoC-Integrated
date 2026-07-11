# Figure Captions

본 문서는 `figures/` 폴더에 저장된 주요 figure를 논문 또는 보고서에 사용할 때 적용할 caption 문구를 정리한다.

모든 figure는 **SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과**를 나타낸다. 따라서 아래 figure들은 transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL bit-exact 등가성 검증을 의미하지 않는다.

## 공통 주의 문구

```text
본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다.
```

## Figure별 권장 Caption

| Figure | 권장 caption / note |
|---|---|
| `fig_matlab_prevalidation_flow` | SystemVerilog XMODEL 구현 전 MATLAB nominal pre-validation과 reference generation의 전체 흐름을 나타낸다. 본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다. |
| `fig_afe_chain_overview` | MATLAB nominal model에서 사용한 AFE+ADC 신호 처리 체인을 나타낸다. 입력 ECG 전압은 HPF, IA, 60 Hz notch, LPF, ADC quantizer를 거쳐 offset-binary ADC code, signed decimal stream, signed two's-complement hex `.mem`으로 변환된다. 본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다. |
| `fig_total_frequency_response` | MATLAB nominal AFE+ADC chain의 전체 frequency response reference를 나타낸다. HPF cutoff, 60 Hz notch target, LPF cutoff를 확인하기 위한 기준 그래프이다. 단, MATLAB time-domain digital notch approximation의 60 Hz ideal zero는 실제 analog attenuation claim이 아니다. 본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다. |
| `fig_notch_dense_sweep` | Active Twin-T 60 Hz notch의 dense frequency-domain reference를 나타낸다. 본 figure는 60 Hz target notch 특성을 보여주며, 50 Hz까지 완전 제거한다고 주장하지 않는다. 본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다. |
| `fig_dynamic_range_headroom` | 대표 NSR/CHF/ARR/AFF 입력에 대한 ADC rail 대비 AFE 출력 headroom을 나타낸다. 모든 클래스에서 clipping ratio가 0%임을 nominal 기준에서 확인하기 위한 figure이다. 본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다. |
| `fig_adc_code_distribution` | 대표 ECG 입력에서 생성된 ADC code distribution을 나타낸다. ADC code가 0 또는 4095 rail에 붙지 않는지 확인하기 위한 figure이며, downstream RTL replay의 canonical format은 signed two's-complement `.mem`이다. 본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다. |
| `fig_reference_vector_handoff` | MATLAB reference vector가 후속 XMODEL 등가성 검증 및 locked digital RTL replay로 전달되는 흐름을 나타낸다. canonical replay vector는 `adc_signed_twos_complement.mem`이다. 본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다. |