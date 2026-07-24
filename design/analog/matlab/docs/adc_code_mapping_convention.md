# ADC Code Mapping Convention 정리

MATLAB ADC output은 12-bit offset-binary code, signed decimal stream, signed 12-bit two's-complement hex `.mem` 세 형태로 저장된다.
최종 downstream digital input contract는 **1 kSPS signed 12-bit ECG stream**이며, 공식 XMODEL/RTL replay format은 **signed 12-bit two's-complement hexadecimal `.mem`**이다.

## 1. 제공하는 reference format

| 파일 | 의미 | 용도 |
|---|---|---|
| `adc_offset_binary.mem` | physical ADC output에 해당하는 12-bit offset-binary code | ADC code convention 확인용 reference |
| `adc_signed.txt` | `adc_offset_binary - 2048`로 변환한 signed decimal stream | signed stream 수치 확인용 reference |
| `adc_signed_twos_complement.mem` | signed stream을 12-bit two's-complement bit pattern으로 encoding한 3자리 대문자 hex `.mem` | 공식 downstream XMODEL/RTL replay format |

`adc_signed_twos_complement.mem`의 각 line은 아래 변환과 동일하다.

```matlab
encoded = mod(adc_signed, 4096);
fprintf(fid, '%03X\n', encoded);
```

## 2. Offset-binary와 signed stream의 관계

```matlab
adc_offset_binary = floor((V + 1.65)/3.3 * 4095);
adc_offset_binary = min(max(adc_offset_binary, 0), 4095);
adc_signed = adc_offset_binary - 2048;
adc_signed_twos_complement = mod(adc_signed, 4096);
```

0 V는 `floor()` 사용 때문에 offset-binary 2047, signed decimal -1로 mapping된다.
+1 LSB 근처의 입력은 offset-binary 2048, signed decimal 0으로 mapping된다.

## 3. Downstream replay convention

최종 digital input contract는 signed 12-bit ECG stream이다.
따라서 RTL replay에는 `adc_signed_twos_complement.mem`을 사용한다.

`adc_offset_binary.mem`은 physical ADC code reference로 보존하지만, signed input을 기대하는 RTL에 직접 넣으면 안 된다.
offset-binary code를 직접 사용하는 별도 testbench에서는 반드시 mid-code subtraction 또는 convention matching을 적용해야 한다.

## 4. Source ECG input code와 AFE ADC output code 구분

`reference_vectors/<CLASS>/input.csv`의 `source_code_signed_est_5uV_per_code`는 원본 ECG 입력 전압 scale을 추적하기 위한 estimate이다.
이 값은 AFE ADC output code가 아니다.

- XMODEL analog input: `reference_vectors/<CLASS>/input.csv`의 `voltage_V`
- Physical ADC code reference: `reference_vectors/<CLASS>/adc_offset_binary.mem`
- Signed decimal reference: `reference_vectors/<CLASS>/adc_signed.txt`
- Canonical XMODEL/RTL replay reference: `reference_vectors/<CLASS>/adc_signed_twos_complement.mem`

## 5. ADC code mapping test

아래 표는 `results_dataset/adc_code_mapping_test.csv`와 동일한 convention을 설명한다.
해당 CSV에는 offset-binary decimal/hex, signed decimal, signed two's-complement hex가 함께 저장된다.

| input_voltage_V | offset_binary_code_decimal | offset_binary_code_hex | signed_decimal | signed_twos_complement_hex | formula | signed_conversion_formula | note |
|---|---|---|---|---|---|---|---|
| -1.65 | 0 | 000 | -2048 | 800 | floor((V + 1.65)/3.3 * 4095), clipped to [0,4095] | signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3) | negative full-scale |
| -1 | 806 | 326 | -1242 | B26 | floor((V + 1.65)/3.3 * 4095), clipped to [0,4095] | signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3) |  |
| -0.000805860805861 | 2046 | 7FE | -2 | FFE | floor((V + 1.65)/3.3 * 4095), clipped to [0,4095] | signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3) |  |
| 0 | 2047 | 7FF | -1 | FFF | floor((V + 1.65)/3.3 * 4095), clipped to [0,4095] | signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3) | 0 V maps to offset-binary 2047 and signed -1 because floor() is used |
| 0.000805860805861 | 2048 | 800 | 0 | 000 | floor((V + 1.65)/3.3 * 4095), clipped to [0,4095] | signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3) |  |
| 1 | 3288 | CD8 | 1240 | 4D8 | floor((V + 1.65)/3.3 * 4095), clipped to [0,4095] | signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3) |  |
| 1.65 | 4095 | FFF | 2047 | 7FF | floor((V + 1.65)/3.3 * 4095), clipped to [0,4095] | signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3) | positive full-scale |
