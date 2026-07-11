# MATLAB-to-XMODEL 인계 문서

이 문서는 MATLAB reference output을 MATLAB-vs-XMODEL 등가성 검증에서 어떻게 사용할지 정의한다.
단, 이 문서는 MATLAB과 XMODEL이 이미 bit-exact하게 일치한다는 의미가 아니다.

## 1. MATLAB AFE 체인 순서

```text
input ECG voltage [V]
→ HPF 0.482 Hz
→ IA ×201
→ 60 Hz notch, Q≈5.0
→ LPF 150.1 Hz
→ ADC ±1.65 V
→ 12-bit offset-binary ADC code
→ signed decimal stream
→ signed 12-bit two's-complement hex .mem
```

## 2. 시간 영역 stream 등가성 기준

XMODEL의 time-domain output은 아래 MATLAB reference와 비교한다.

- `reference_vectors/<CLASS>/matlab_stage_outputs.csv`
- `reference_vectors/<CLASS>/adc_offset_binary.mem`
- `reference_vectors/<CLASS>/adc_signed.txt`
- `reference_vectors/<CLASS>/adc_signed_twos_complement.mem`

| Metric | 목표 / 설명 |
|---|---|
| sample alignment | lag = 0 sample |
| RMS LSB error | convention을 맞춘 뒤 가능하면 2–3 LSB 이하 |
| max abs LSB error | outlier 확인 |
| correlation | 0.99 이상 권장 |
| ADC code convention | MATLAB과 XMODEL의 offset-binary convention 일치 여부 확인 |
| signed stream convention | MATLAB과 XMODEL의 signed 12-bit convention 일치 여부 확인 |
| canonical replay file | `adc_signed_twos_complement.mem` 기준 |

## 3. Active Twin-T notch 주파수 응답 기준

60 Hz notch의 parameter-level / frequency-domain reference는 아래 결과와 비교한다.

- `docs/notch_60hz_reference.md`
- `results_dataset/notch_dense_sweep.csv`
- `results_dataset/notch_dense_sweep_metrics.csv`

MATLAB time-domain stream은 digital Q≈5 notch approximation을 사용한다.
반면 dense notch sweep은 active Twin-T 구조의 frequency-domain reference를 제공한다.
두 결과는 서로 관련되어 있지만, 동일한 비교 대상은 아니다.
따라서 XMODEL 검증에서는 time-domain stream equivalence와 notch frequency-response validation을 분리해서 확인해야 한다.

## 4. Input / Output convention

- XMODEL analog input은 `reference_vectors/<CLASS>/input.csv`의 `voltage_V`를 사용한다.
- `source_code_signed_est_5uV_per_code`는 source ECG scale 추적용 estimate이며, AFE ADC output code가 아니다.
- `adc_offset_binary.mem`은 physical ADC offset-binary code convention 확인용 reference이다.
- `adc_signed.txt`는 offset-binary code에서 mid-code 2048을 제거한 signed decimal stream reference이다.
- `adc_signed_twos_complement.mem`은 공식 downstream XMODEL/RTL replay format이다.
- 최종 digital input contract는 1 kSPS signed 12-bit ECG stream이다.

## 5. Canonical downstream replay format

수환 XMODEL 저장소와 양건 locked digital RTL testbench의 최종 interface는 아래 형식으로 확정되었다.

```text
1 kSPS signed 12-bit two's-complement hexadecimal .mem
one sample per line
3 uppercase hex digits per line
```

`adc_signed_twos_complement.mem`은 아래 MATLAB 변환과 동일하다.

```matlab
encoded = mod(adc_signed, 4096);
fprintf(fid, '%03X\n', encoded);
```

따라서 offset-binary code를 RTL에 직접 넣지 않는다.
offset-binary code를 사용하는 별도 테스트 경로가 있다면 명시적인 mid-code subtraction 또는 convention matching을 적용해야 한다.

## 6. Reference vector 검증

`reference_vectors/reference_vector_manifest.csv`는 모든 reference vector 파일의 byte 수와 SHA256을 기록한다.
line ending 차이로 hash가 바뀌지 않도록 `.gitattributes`에서 reference vector 파일의 line ending을 LF로 고정한다.
검증은 아래 MATLAB script로 수행한다.

```matlab
verify_reference_vector_manifest
```

하나라도 파일 누락, byte 수 불일치, SHA256 불일치가 발생하면 warning이 아니라 MATLAB error로 실패한다.