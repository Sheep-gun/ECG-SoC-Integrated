# AFE–디지털 ADC 인터페이스 결정: XADC vs 커스텀 SAR ADC

**작성:** 이수환 (AFE) · **일자:** 2026-06-26 · **수신:** 디지털/알고리즘팀
**결론:** FPGA 데모는 **AFE만 외부 + XADC 수신**. 커스텀 SAR ADC는 **비합성 SoC/ASIC 설계물**로 유지. 학습/데모는 **현 SAR-AFE 데이터로 일관 사용**(라이브 XADC가 스코프에 없어 XADC 재학습 불필요). 실제 물리 XADC 연동 시엔 **AFE 이득을 ×201→×61로 조정**하면 재학습 없이 동일 코드 스케일 유지.

---

## 1. 두 ADC 방식 비교

| 방식 | 내용 | 필요 하드웨어 | 난이도 |
|---|---|---|---|
| **(1) XADC** | FPGA 내장 ADC 사용 | **AFE 아날로그 회로만** 외부 | 낮음 (현실적) |
| (2) 커스텀 SAR | 외부 물리 ADC 칩 필요 (현재 SV는 시뮬 전용=비합성) | AFE + 외부 SAR 칩 (= 실제 SoC/ASIC 설계) | 급격히 높음 |

→ **(1) XADC 채택.** 커스텀 SAR ADC는 **ASIC/SoC 설계 기여물**(XModel로 검증 완료)로 유지하되 FPGA에는 올리지 않음.

## 2. "XADC든 SAR든 디지털 입력 데이터가 같은가?" → 인터페이스는 같고, **스케일은 다름**

| 항목 | 커스텀 SAR ADC | XADC (Nexys A7 / 7-series) |
|---|---|---|
| 비트/속도 | 12-bit / 1 kSPS | 12-bit / 최대 1 MSPS (1kSPS로 데시메이션) |
| 입력 범위 | ±1.65 V (span 3.3 V) | **bipolar ±0.5 V** 또는 unipolar 0–1 V (span 1 V) |
| **LSB (코드당 전압)** | **805.7 µV/code** (3.3V/4096) | **244.1 µV/code** (1.0V/4096) |
| 0점 | offset-binary, mid=2048 (→ −2048 어댑터로 signed) | bipolar=2's complement(0중심) / unipolar=offset(−2048) |

- core 포트(`signed [11:0] adc_data`, 1kSPS) **인터페이스 형식은 동일**하게 맞출 수 있음(어댑터는 사소).
- 그러나 **LSB 비율 = 805.7 / 244.1 = 3.30** → 같은 전압이라도 코드 수가 약 3.3배 차이.

## 3. 왜 스케일이 분류에 결정적인가 (RTL 근거)

`digital/ecg_event_encoder.v`, `digital/qrs_lif_detector.v` 확인:
- `delta = adc_data − prev_sample` (코드 단위 차분) → `strong_event = (|delta| > T_EVENT)` — **T_EVENT 고정 정수**
- QRS LIF: `mem += W_EVENT`, leak `LEAK_QRS`, 발화 `T_QRS`, 불응 `T_REF` — **전부 고정 정수 임계값**
- **적응형/AGC/정규화 없음.**

∴ ADC 코드 진폭이 3.3배 커지면 `delta`도 3.3배 → 고정 임계값이 다르게 트리거 → 분류 붕괴.
**"raw XADC 코드"와 "raw SAR 코드"는 분류기에게 서로 다른 데이터가 맞음.** (팀원 의문이 타당함)

## 4. 구체 산출 수치 (핵심)

**현재(학습된) 정준 코드 스케일 = 커스텀 SAR 경로:**
```
AFE 전압이득 G_SAR        = ×201
SAR LSB                   = 3.3V / 4096          = 805.7 µV/code
입력환산 코드밀도          = 201 / 0.8057mV       = 249.5 codes / (입력 mV)
입력 다이내믹레인지(±2048) = ±2048 / 249.5        = ±8.21 mV  (전극 입력 기준)
```

**XADC로 "재학습 없이" 동일 스케일을 얻는 조건 (bipolar ±0.5 V):**
```
조건: G_XADC / LSB_XADC = G_SAR / LSB_SAR  (코드밀도 일치)
G_XADC = G_SAR × (V_XADC_half / V_SAR_half) = 201 × (0.5 / 1.65) = 60.9  →  ★ AFE 이득 ≈ ×61
검산: 60.9 / 0.2441mV = 249.5 codes/입력mV  → SAR와 동일 ✓
입력 다이내믹레인지: ±0.5V / ×61 = ±8.2 mV  → SAR와 동일 ✓ (클리핑 여유 충분)
0점: bipolar는 0V→mid 자동 (AFE 출력이 HPF로 0중심이라 별도 바이어스 불필요)
```

**핵심 공식:**  `G_XADC = G_SAR × (V_XADC_half / V_SAR_half) = 201 × 0.5/1.65 ≈ 61`

**만약 AFE 이득을 ×201로 유지하면 (비권장):**
```
- XADC 코드밀도 = 201 / 0.2441mV = 823 codes/mV  → SAR의 3.30배 (스케일 불일치)
- 게다가 ±0.5V / ×201 = ±2.49 mV 에서 클리핑 → ECG R-peak(>2.5mV)에서 포화 (사용 불가)
- ∴ 이득 축소는 필수. 굳이 ×201 유지 시 on-chip 리스케일 필요:
    canonical = xadc_signed × (244.1/805.7) = × 0.3030
    고정소수점: × 155 >> 9  (= 0.3027, 오차 0.1%)
```

**unipolar 0–1 V 사용 시:** 이득은 동일 ×61, 단 0V→0.5V로 **+0.5 V DC 바이어스** 추가해 mid-code(2048) 정렬 필요. → **bipolar ±0.5 V가 더 깔끔(바이어스 불필요), 권장.**

**XADC 샘플링:** XADC는 ~1 MSPS이므로 1 kSPS로 **데시메이션**(예: 1kHz 트리거 또는 N샘플 평균 — 평균 시 SNR 개선 보너스).

## 5. 학습/데모 정합 — 우리 스코프에선 XADC 재학습 불필요

- 확정 스코프 = **XModel 통합 시뮬 + FPGA playback(ROM .mem 재생)**. **라이브 XADC가 경로에 없음**(playback은 ROM 데이터를 코어에 직접 주입).
- 따라서 **"학습 데이터 == playback ROM 데이터"** 만 동일하면 정합. 현 **SAR-AFE 데이터(`afe_output_xmodelmatch`)로 학습 + 동일 데이터를 ROM에** 넣으면 완결 → **XADC 재학습 불필요.**
- XADC↔SAR 스케일 불일치는 **라이브 XADC-in-loop 데모에서만** 문제이며, 그건 스코프 밖(실시간 전극 시연 폐기).

## 6. 미래 대비 (라이브 ADC 연동 시에만)

선택 A — **AFE 이득으로 정합(권장):** AFE를 ×61로 만들어 XADC 출력이 정준 스케일과 동일 → 재학습·on-chip 연산 불필요.
선택 B — **on-chip 정준 리스케일:** ADC 직후 `canonical = adc × 0.303`(×155>>9) 적용 → SAR/XADC 무관하게 분류기에 동일 데이터. (manifest의 `ptp`/`abs95`로 진폭정규화 인프라 존재)

## 7. 권장 요약
1. FPGA 데모: AFE 외부 + **XADC(bipolar ±0.5V)** 수신, **AFE 이득 ×61**(=201×0.5/1.65).
2. 커스텀 SAR ADC = ASIC/SoC 설계물(XModel 검증)로 유지. ASIC=커스텀 SAR / FPGA=XADC, 둘 다 동일 **정준 12-bit signed 스케일(249.5 codes/mV, ±8.2mV FS)**.
3. 학습/playback: **현 `afe_output_xmodelmatch`로 일관** — XADC 재학습 안 함(라이브 XADC 미사용).
