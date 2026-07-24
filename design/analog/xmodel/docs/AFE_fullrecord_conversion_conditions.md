# Full-record AFE+ADC 변환 조건 (디지털팀 전달)

**작성:** 이수환 (AFE) · **일자:** 2026-06-27 · **대상:** record 전체 stream AFE+ADC 변환본

요청대로 각 record를 **60초로 자르지 않고 전체 stream** 그대로 AFE+ADC 변환했습니다.
변환 조건은 기존 60초 `xmodelmatch`와 **완전히 동일**하며, 추가로 full-record용으로 검증했습니다.

## 1. 파이프라인
```
WFDB ch0(ECG1) digital → 선형보간(linear) 1kSPS 리샘플
   → AFE: ÷200000(V) → HPF(0.482Hz) → IA(×201) → 60Hz notch(Q5) → LPF(150Hz)
   → ADC: code = trunc((V+1.65)/3.3 × 4095), clip[0,4095]
   → signed 12-bit 출력 (= unsigned − 2048)
```

## 2. 요청 항목별 답변 (email 4번)
| 항목 | 값 |
|---|---|
| **AFE filter** | HPF 0.482Hz · IA gain ×201 · 60Hz Twin-T notch(Q≈5, 80dB) · LPF 150Hz |
| **ADC Vref** | ±1.65 V (full-scale span 3.3 V) |
| **ADC offset 기준** | offset-binary, mid-code **2048**. **signed = unsigned − 2048** |
| **signed/unsigned 변환** | 제공본은 **signed 12-bit(2의보수, 0중심)**. unsigned 필요시 `unsigned = signed + 2048` (0~4095) |
| **input ECG voltage scaling** | `V = code / 200000` (1 code ≈ 5 µV, ÷200000) |
| **sample rate** | **1000 SPS** (native에서 **선형보간** 리샘플) · native: nsrdb 128 / mitdb 360 / afdb 250 / chfdb 250 Hz |
| **앞 2초 HPF settling** | 제공본은 **자르지 않음**(전체 stream 보존). record **맨 앞 ~2초(2000샘플)**만 HPF 과도구간(5τ≈1.65s). manifest `settling_skip_sec=2`. **연속 stream이라 record 중간 60s 스냅샷은 settling 없음**(스냅샷마다 정착구간 없음 — 학습 세그먼트보다 오히려 깨끗) |
| **XModel bit-exact vs emulator** | **검증된 emulator**. 실제 XModel(Questa+XModel) 대비 평균 RMS 2.01 LSB(8세그)로 검증된 XModel-정합 에뮬레이터. full-record 출력은 기존 xmodelmatch와 **2s 정착 후 1 LSB 내 일치**. bit-exact XModel은 아니나 검증된 등가 |

## 3. 형식 (email 2번)
- record 1개당 `.mem` 1개, **record 전체 길이 그대로**, 60초 분할 없음.
- 1 kSPS, signed 12-bit (3-hex, Verilog `$readmemh` 호환 — 기존 .mem과 동일 포맷).
- 디지털 core 입력에 바로 사용 가능.

## 4. 일관성 검증 (중요)
- **리샘플**: 선형보간이 기존 60s `.mem` 데이터셋과 **100% 동일**(RMS 0, 검증 완료) → 이 full-record stream에서 60s 스냅샷을 잘라도 **학습 데이터 조건과 일치**.
- **AFE 출력**: full-record AFE를 기존 xmodelmatch 세그먼트와 비교 → 2s 정착 후 **RMS 0.40 LSB, max 1 LSB** 일치.
- **per-segment median centering 미적용**: 연속 stream이라 세그먼트 단위 센터링은 하지 않음. AFE HPF가 baseline을 제거하므로 결과 동등(위 1 LSB 일치로 입증). 디지털팀이 60s 스냅샷을 자른 뒤 별도 센터링이 필요하면 적용 가능하나, HPF 때문에 불필요.

## 5. manifest 컬럼 (email 3번)
`split, class_label, record_id, source_db, original_record_file, afe_adc_mem_file, sample_rate, adc_format, total_samples, total_duration_sec, settling_skip_sec, notes`

## 6. split 관련 확인 요청
- `split`은 기존 `strict60_large` manifest의 record→split 매핑에서 도출했습니다.
- 단, handoff에 포함된 record 중 일부는 기존 strict split pool에 없어 **`unassigned`**로 표기된 것이 있습니다. 해당 record들의 train/val/test 배정은 **디지털팀 기준으로 확정해 주세요**(원하시면 매핑 표 주시면 반영하겠습니다).
