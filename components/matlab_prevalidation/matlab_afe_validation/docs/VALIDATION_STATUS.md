# 검증 상태 정리

이 문서는 MATLAB repo가 주장할 수 있는 범위와 후속 XMODEL/digital 파트로 넘겨야 하는 범위를 정리한다.

| Item | Status | Artifact | Note |
|---|---|---|---|
| Parameter reference | PASS | `docs/afe_adc_parameter_reference.md` | XMODEL nominal 기준 |
| Frequency response reference | PASS | `docs/frequency_response_reference.md` | 60 Hz ideal digital zero caveat 및 passband-relative column 포함 |
| Dense 60 Hz notch reference | PASS/PARTIAL | `docs/notch_60hz_reference.md` | bandwidth/Q는 nominal estimate, physical Q 아님 |
| Dynamic range / headroom | PASS | `docs/dynamic_range_headroom_reference.md` | representative inputs 기준 clipping 0% |
| ADC code mapping | PASS | `docs/adc_code_mapping_convention.md` | offset-binary, signed decimal, signed two's-complement hex convention 명시 |
| Downstream canonical replay format | PASS | `reference_vectors/<CLASS>/adc_signed_twos_complement.mem` | 1 kSPS signed 12-bit two's-complement hex `.mem`, 한 줄당 3자리 대문자 hex |
| Reference vectors | PASS | `reference_vectors/reference_vector_manifest.md` | NSR/CHF/ARR/AFF SHA256 tracked, signed two's-complement `.mem` 포함 |
| Reference vector manifest verification | PASS | `verify_reference_vector_manifest.m` | 파일 존재 여부, byte 수, SHA256 불일치 시 MATLAB error |
| Input dataset source traceability | PARTIAL | `docs/INPUT_DATASET_MANIFEST.md` | source database/record는 기록, exact segment start는 이 MATLAB repo에서 not tracked |
| MATLAB-vs-XMODEL equivalence | NOT DONE | XMODEL 담당 | claim 금지 |
| CMRR / op-amp / ADC nonideal | NOT DONE | XMODEL 또는 analog stress 검증 | claim 금지 |
| PCB / silicon / clinical validation | NOT DONE | scope 밖 | claim 금지 |
| Board replay / final classification accuracy | NOT DONE | digital/integration 담당 | MATLAB repo 범위 밖 |

## 최종 claim

MATLAB 단계는 SystemVerilog XMODEL 구현 이전의 nominal system-level pre-validation 및 reference generation 단계이다.
본 단계는 schematic 기반 AFE 필터 파라미터, frequency-response reference, ADC headroom, code-mapping convention, 그리고 대표 NSR/CHF/ARR/AFF 입력에 대한 SHA256-tracked reference vector를 정의한다.
본 단계는 transistor-level, PCB-level, silicon-level, clinical validation 또는 MATLAB-vs-XMODEL bit-exact equivalence를 주장하지 않는다.