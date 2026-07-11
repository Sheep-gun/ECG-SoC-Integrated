# [전달] AFE 통합검증 상세 — 디지털/알고리즘팀 요청 6개 항목 회신

**작성:** 이수환 (AFE / 통합검증) · **수신:** 디지털(양건) · 알고리즘팀 · **일자:** 2026-06-25
**근거:** `~/ECG-SoC` 실제 코드·로그(2026-06-25 재실행) + `person_data_record_split_strict_varlen` 데이터셋
**한 줄 결론:** 통합 시뮬은 **에러 0**으로 완전 동작. 분류 이슈는 2종 — ① **NSR→ARR은 AFE와 무관한 분류기 baseline 오류**, ② **ARR→AFF만 AFE(대역통과 필터링) 유발**. 둘 다 해법은 분류기 재학습.

---

## 📌 먼저: class code mapping (요청 5 — 가장 중요)

**`pred_class 0=NSR, 1=CHF, 2=ARR, 3=AFF` 가 맞습니다.** 3개 독립 출처로 확정:
1. `tb/tb_mixed_signal.sv` 주석(L8): `pred_class (0=NSR 1=CHF 2=ARR 3=AFF)`
2. **데이터셋 manifest** `dataset_manifest_*_varlen_meta.csv`의 `class_id` 열: NSR=0, CHF=1, ARR=2, AFF=3
3. 디지털 단독 기준(digref)이 팀원 공식 RTL CSV와 4/4 일치(셋업 검증됨)

### ❗ "integration_report에 NSR이 2로 적힌 건 오타인가?" → **오타 아님. 표의 의미 오해입니다.**

`docs/integration_report.md` §7 표:

| 클래스(입력) | ① 디지털 단독(원본 .mem) | ② AFE 통합(라이브) | ③ 일치 |
|---|---|---|---|
| NSR | **2** | **2** | ✅ |
| CHF | 1 | 1 | ✅ |
| ARR | 2 | 3 | ❌ |
| AFF | 3 | 3 | ✅ |

- **열 ①** = AFE 없이 원본 .mem을 분류기에 직접 넣은 결과
- **열 ②** = AFE를 통과시킨 결과
- **열 ③ "일치" = ①과 ②가 같은가(= AFE가 분류기에 투명한가)** — **정답(ground truth)과 일치하는지가 아님!**

따라서 `NSR | 2 | 2 | ✅`의 뜻은:
> "NSR 레코드를 넣으면 **AFE 없이도 분류기가 이미 2(ARR)로 오분류**하고, AFE를 통과시켜도 똑같이 2다. 둘이 같으므로(=AFE 투명) ✅."

**핵심:** `NSR→2`는 **AFE가 만든 오류가 아니라 분류기 baseline 자체의 오류**입니다(이 NSR 대표 레코드=16539). **AFE가 실제로 바꾼 것은 ARR(2→3) 단 하나**입니다.

### 정답 기준 정확도(대표 4레코드)
| | 정답 | 디지털 단독 | AFE 통합 |
|---|---|---|---|
| NSR(16539) | 0 | 2 ❌ | 2 ❌ |
| CHF(chf05) | 1 | 1 ✅ | 1 ✅ |
| ARR(105) | 2 | 2 ✅ | 3 ❌ |
| AFF(04015) | 3 | 3 ✅ | 3 ✅ |
| **정확도** | | **3/4** | **2/4** |

> ⚠️ 이는 **클래스당 대표 1레코드** 결과입니다. 전체 정확도는 요청 1의 전체 데이터셋으로 평가해야 합니다(아래).

---

## 1. 전체 strict dataset AFE 출력 데이터 (생성 완료)

요청대로 **record-wise train/val/test 전체**에 AFE를 통과시킨 ADC 결과를 생성했습니다.

**위치:** `바탕 화면\디지털 설계 블록 양건\afe_output_strict\`
```
afe_output_strict/
├── train/  signed/*.mem  unsigned/*.mem   (400 segments)
├── val/    signed/*.mem  unsigned/*.mem   (160 segments)
├── test/   signed/*.mem  unsigned/*.mem   (160 segments)
├── afe_manifest_train.csv
├── afe_manifest_val.csv
└── afe_manifest_test.csv
```
- **`signed/`** = 2의보수 signed 12-bit (digital core 입력 직결용, 원본 .mem과 동일 포맷 → `$readmemh` 드롭인 교체)
- **`unsigned/`** = offset-binary unsigned 12-bit (raw AFE ADC 출력 포맷, = signed + 2048)
- 파일명은 원본과 동일(`{segment_id}_{class}_{record}_{dur}s_{start}ms.mem`)

**manifest CSV 열(요청 형식 충족):**
`segment_id, record_id, class_label, class_id, raw_mem_file, afe_adc_signed_file, afe_adc_unsigned_file, start_time_s, duration_s, n_samples`

**적용 필터:** `scripts/filter_mem.py "full"` 과 **동일 계수**의 AFE 등가 선형필터
(HPF 0.48Hz → 60Hz notch Q5 → LPF 150Hz). 이 필터는 격리실험에서 **XModel AFE 통합결과를 정확히 재현**함이 입증됨(`digref_full == AFE_integration`, full→NSR2 CHF1 ARR3 AFF3). 즉 느린 XModel AFE(레코드당 ~2-3분)를 전수 돌리는 대신, **검증된 등가 디지털 필터로 720 segment 전체를 일관 생성**한 것입니다. (XModel 풀-AFE는 대표 4레코드에 교차검증용으로 실행.)

> **알고리즘팀 권장 사용법:** `afe_output_strict/train/signed/` 로 재학습 → `val`,`test`로 평가.
> 이렇게 하면 "AFE 통과 신호 기준" 실제 4클래스 정확도와 NSR/ARR 취약 레코드 영향을 정량화할 수 있습니다.

---

## 2. AFE 변환 조건 (raw .mem → analog PWL) — `scripts/convert_mem.py`

| 항목 | 값 |
|---|---|
| **signed_code → voltage 변환식** | `voltage = signed_code / 200000` [V]  (signed_code = hex<2048 ? hex : hex−4096) |
| **입력 ECG amplitude scale** | 1 code ≈ **5 µV**, ±600 code ≈ **±3 mV** (= AFE 차동입력 `v_ecg_pos`, `v_ecg_neg=0`) |
| **sample rate** | **1 kSPS** (1 ms 간격) |
| **PWL interpolation** | **선형보간(linear)**, UP=4 → 250 µs 점 간격 (ZOH 계단 아티팩트 제거) |
| **ADC Vref** | **±1.65 V** (Vfull = 3.3 V) |
| **ADC offset 기준** | **2048** (mid-scale), offset-binary |
| **ADC 변환식** | `code = ((Vin + 1.65) / 3.3) × 4095`, 12-bit |

- AFE 내부: 입력(±3mV) → IA **×201** → 노치/LPF → SAR ADC. 라운드트립 진폭은 ≈보존(상관도 0.90~0.97, AFE출력 코드범위 ≈ 원본 .mem 코드범위).

---

## 3. 최종 AFE filter 파라미터 (코드 실측값 — 보고서와 일치 확인)

`analog/ecg_afe_xmodel.sv`의 **실제 부품 인스턴스**(주석 아님) 기준:

| 항목 | 값 | 코드 위치 / 산출 |
|---|---|---|
| **HPF cutoff** | **0.482 Hz** | C1/C2=33nF, R6/R3=10MΩ (L191–196); fc=1/(2π·33n·10M) |
| **LPF cutoff** | **150 Hz** | R_lpf=1kΩ, C_lpf=**1.06µF** (L331–332, Bug#12 적용됨) |
| **notch frequency** | **60.0 Hz** | Twin-T RT=26.526kΩ, CB=100nF, CT=200nF, RB=13.263kΩ (L298–305) |
| **notch Q** | **≈5** (depth 80dB) | 능동 부트스트랩 k=0.95: Rk1=5kΩ, Rk2=95kΩ (L326–327) |
| **AFE gain** | **201** | IA 1단 1+2×100k/1k=201, 2단 차동 ×1 (R2=R4=100k, Rg=1k, R5–R9=10k) |
| **ADC resolution** | **12-bit** | offset-binary, code=((Vin+1.65)/3.3)×4095 (L355–368) |
| **ADC sampling rate** | **1 kSPS** | clk_samp 1kHz |
| 공급전압 | ±1.65 V | (L88–89) |
| CMRR | 156 dB(모델) | (실측은 저항매칭 한계) |
| 통과대역 | 3–45Hz 평탄, −3dB=150Hz | 특성측정 검증 |

✅ **코드 ↔ 보고서/스펙표 전부 일치.**
⚠️ 단, **L43 주석 1곳**이 옛 값(`C=1µF → fc=159Hz`)으로 남아있음 — 실제 인스턴스(L332)는 `1.06µF/150Hz`. **주석만 수정 권장**(동작·스펙엔 영향 없음).

---

## 4. mixed-signal simulation 원본 결과 (raw log)

**실행:** `bash scripts/run_mixed_all.sh 60` (2026-06-25 재현) · **raw log:** `~/ECG-SoC/sim_out/mixed_fullchain.log`

```
[NSR] MIXED_RESULT pwl=ecg_NSR.pwl startsec=2.0 endsec=60.0 pred_valid=1 pred_class=2 | Errors: 0
[CHF] MIXED_RESULT pwl=ecg_CHF.pwl startsec=2.0 endsec=60.0 pred_valid=1 pred_class=1 | Errors: 0
[ARR] MIXED_RESULT pwl=ecg_ARR.pwl startsec=2.0 endsec=60.0 pred_valid=1 pred_class=3 | Errors: 0
[AFF] MIXED_RESULT pwl=ecg_AFF.pwl startsec=2.0 endsec=60.0 pred_valid=1 pred_class=3 | Errors: 0
```
- **XModel/Questa log:** FLEXlm `FEATURE 'XMODEL' checked out` 정상, **Errors: 0 / Warnings: 4**(무해), pred_valid=1, 클래스당 ~2–3분.
- **class mapping:** 0=NSR 1=CHF 2=ARR 3=AFF (위 §5 확정)
- **AFE ADC output log:** `scripts/run_afe_sim.sh` → `adc_output.txt`, 클래스별 `sim_out/multiclass/adc_{NSR,ARR,AFF,CHF}.txt` 보유. 전계층 파형(VCD)은 `make vcd`로 생성 가능.
- **입출력 waveform 캡처:** 현재 텍스트 ADC 로그/VCD 형태로 보유. 이미지 캡처가 필요하면 요청 주세요(VCD→파형 캡처 추출).

> 통합 메커니즘(AFE→어댑터→core)은 완전 동작. 어댑터: ①`core_adc = {~afe_adc[11], afe_adc[10:0]}`(offset→signed), ②매 샘플 sample_valid·rhythm_tick 펄스 생성.

---

## 5. (위 상단 📌에서 상세) — 요약
- 매핑 0/1/2/3 = NSR/CHF/ARR/AFF **확정**.
- integration_report의 NSR=2는 **오타 아님**. "일치" 열은 AFE 투명성(①=②)이지 정답 일치가 아님.
- **NSR→ARR = 분류기 baseline 오류(AFE 무관)**, **ARR→AFF = AFE 대역통과 필터링 유발**.

---

## 6. 실제 보드 연동 계획 (현황 + 미결정 사항)

**현황(AFE 측 사실):**
- 현재 FPGA 데모(`nexys_a7_model_s_smoke_top.v`)는 **내장 ROM(demo_*.mem) 재생 방식**으로 AFE 미연결(독립 데모).
- XModel AFE(`ecg_afe_xmodel.sv`)는 **비합성 행동모델** → FPGA에 합성 불가. 실제 보드의 AFE는 **물리 아날로그 회로**(회로도 참조: `ECG_AFE_LTspice\ecg_afe.asc`).
- AFE 출력 포맷: **12-bit, 1 kSPS**, offset-binary unsigned (또는 어댑터 후 signed) — core가 기대하는 형식과 §2/§3대로 정합.

**실제 연동에 필요한 결정 사항(⚠️ 디지털/시스템팀 결정 필요 — 현재 미정):**

| 항목 | 질문 | 비고 |
|---|---|---|
| AFE→FPGA 진입점 | 물리 AFE 출력이 보드 어디로? | 현재 미연결(ROM 데모) |
| ADC 방식 | **외부 ADC 칩** vs **FPGA 내장 XADC**? | Nexys A7는 XADC(12-bit) 보유. 외부 SAR ADC(SPI) 대안 |
| ADC clock 생성 주체 | 1 kSPS 샘플클럭을 누가? | FPGA 분주 or ADC 칩 자체 |
| ADC data format | core 입력은 signed 12-bit | 외부 ADC가 offset-binary면 on-FPGA `−2048` 변환 |
| FPGA pin map | AFE/ADC 핀 할당 | **미정 — 보드 설계 시 확정 필요** |

> **AFE 측 제공 가능:** 아날로그 AFE 회로도(LTspice), ADC 인터페이스 스펙(12b/1kSPS/Vref±1.65V/offset-binary), signed 변환 어댑터 로직.
> **결정 요청:** 외부 ADC vs XADC 방식과 핀맵은 보드 담당이 정해주시면 AFE 출력단을 거기에 맞추겠습니다.

---

## 제공 산출물 요약
- `afe_output_strict/` — **전체 데이터셋 AFE 출력**(signed/unsigned .mem) + manifest CSV 3개 (요청 1)
- `scripts/convert_mem.py`(변환조건) · `scripts/filter_mem.py`(AFE 등가필터) (요청 2)
- `analog/ecg_afe_xmodel.sv` + 본 문서 §3 표 (요청 3)
- `sim_out/mixed_fullchain.log` + `adc_*.txt` (요청 4)
- `ECG_AFE_LTspice/ecg_afe.asc` — 물리 AFE 회로도 (요청 6)

## 권장 다음 단계 (알고리즘팀)
1. `afe_output_strict/train/signed/` 로 SNN **재학습** → `val`/`test` 평가.
2. 전체 데이터셋 기준 정확도/혼동행렬 산출 → NSR baseline 오류·ARR 취약레코드(105) 영향 정량화.
3. (선택) 디지털 core를 `afe_output_strict` 전수로 시뮬해 RTL 레벨 정확도 확인 — AFE 측에서 배치 지원 가능.
