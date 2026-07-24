# AFE 최초 입력 데이터셋 (MATLAB용)

> AFE에 **주입한 원본 digitized ECG**(AFE 처리 이전 신호)를 MATLAB에서 바로 쓰도록 CSV로 변환한 것.
> 담당: 이수환(AFE) · 2026-07-07 · 요청: MATLAB 통합 팀원

## 1. 이게 뭐냐
우리 AFE(`analog/ecg_afe_xmodel.sv`)의 **입력단에 넣는 신호**입니다. AFE는 이 ECG를 전압으로 받아
HPF→IA→notch→LPF→ADC를 거칩니다. 즉 **이 CSV = AFE 파이프라인 이전의 raw 입력**.
MATLAB에서 AFE를 모델링하려면 이 신호를 입력으로 넣고 아래 §4 파라미터로 필터체인을 구성하면 됩니다.

## 2. 파일 (4클래스 대표 레코드, 각 60초 @ 1 kSPS)
**두 포맷 제공** — 같은 신호를 (a) 분석용 `.csv`와 (b) XModel/SPICE 주입용 `.pwl`로.

| 클래스 | `.csv`(분석용) | `.pwl`(주입 자극) | 샘플수 | code 범위 | 전압 범위 |
|---|---|---|---|---|---|
| 정상(NSR) | `afe_input_NSR.csv` | `afe_input_NSR.pwl` | 60000 | −98 ~ 424 | −0.49 ~ 2.12 mV |
| 울혈성심부전(CHF) | `afe_input_CHF.csv` | `afe_input_CHF.pwl` | 60000 | −318 ~ 626 | −1.59 ~ 3.13 mV |
| 부정맥(ARR) | `afe_input_ARR.csv` | `afe_input_ARR.pwl` | 60000 | −604 ~ 502 | −3.02 ~ 2.51 mV |
| 심방세동(AFF) | `afe_input_AFF.csv` | `afe_input_AFF.pwl` | 60000 | −389 ~ 368 | −1.95 ~ 1.84 mV |
| MIT-BIH rec100(NSR) | `afe_input_record100_NSR.csv` | `afe_input_record100_NSR.pwl` | 3600 | (360Hz native) | XModel 단일-레코드 주입본 |

> `.pwl`은 XModel AFE 테스트벤치에 실제 주입하는 자극 파일(`data/ecg_*.pwl`과 동일 생성경로).
> `.csv`와 **동일 신호**이며, PWL은 샘플 사이를 ×4 선형보간(0.25ms 간격)한 것.

## 3. 포맷
`afe_input_{class}.csv` 컬럼:
```
sample_index, time_s, code_signed, voltage_V
```
- `code_signed`: **2의보수 signed 12-bit** ADC 코드 (−2048 ~ +2047). 원본 `.mem`의 hex를 디코드한 값.
- `voltage_V`: AFE 입력 전압 = **code_signed / 200000** (1 code ≈ 5 µV). AFE `.sv`가 실제 주입하는 값.
- `time_s`: sample_index / 1000 (fs = **1000 Hz**).
- `afe_input_record100_NSR.csv`는 native 360Hz PWL 기반이라 `time_s, voltage_V, code_signed_est` 컬럼.

`.pwl` 포맷: `time[s] \t voltage[V]` (공백/탭 구분, 헤더 없음). SPICE/XModel PWL 소스로 바로 사용.

## 4. AFE 파이프라인 파라미터 (MATLAB 모델링용)
이 입력에 아래 순서로 적용하면 우리 AFE와 동일:
```
V = code/200000
1) HPF   1차, fc = 0.482 Hz          (baseline 제거; RC=330ms, 앞 ~2s 정착)
2) IA    이득 ×201                    (계기증폭기)
3) Notch 60Hz Twin-T, Q ≈ 5, 80dB    (전원선 간섭)
4) LPF   1차, fc = 150 Hz             (안티에일리어싱)
5) ADC   12-bit, Vref ±1.65V:
         code_unsigned = floor((V + 1.65)/3.3 * 4095), clip[0,4095]
         code_signed   = code_unsigned − 2048
```
검증된 파이썬 등가 구현: `scripts/afe_emu.py` (동일 계수). AFE 출력(디지털팀 .mem)과 비교하려면 이걸 참고.

## 5. MATLAB 로드 예시
```matlab
T = readtable('afe_input_NSR.csv');
v = T.voltage_V;            % AFE 입력 전압 [V]
fs = 1000;                  % 샘플레이트
t  = T.time_s;

% (또는) PWL 직접 로드: P = readmatrix('afe_input_NSR.pwl'); t=P(:,1); v=P(:,2);

% 예) AFE 필터체인 모델 (1차 HPF/LPF)
[bh,ah] = butter(1, 0.482/(fs/2), 'high');
[bl,al] = butter(1, 150/(fs/2),  'low');
% 60Hz 노치
wo = 60/(fs/2); bw = wo/5;  % Q=5
[bn,an] = iirnotch(wo, bw);

y = filter(bh,ah, v);       % HPF
y = 201 * y;                % IA
y = filter(bn,an, y);       % notch
y = filter(bl,al, y);       % LPF
code = min(max(floor((y+1.65)/3.3*4095),0),4095) - 2048;  % ADC signed
```
> 참고: 위 iirnotch/butter는 근사이고, 우리 XModel AFE는 능동 Twin-T·부트스트랩까지 반영. 정밀 비교는 `scripts/afe_emu.py`(bilinear 계수) 기준으로.

## 6. 출처 / 전체 데이터셋
- 이 4개는 **4클래스 대표 레코드**(NSR 16539 · CHF chf05 · ARR 105 · AFF 04015 계열), mixed-signal 통합검증에 사용한 것과 동일.
- 원본 `.mem`: `data/mem_{class}.mem`, 주입 PWL: `data/ecg_{class}.pwl` (repo에는 `.gitignore`로 제외 — 대용량).
- **전체 record별 dataset**(train/val/test 수백 세그)은 `datasets/strict60_large/raw/`에 있으나 gitignore(1.6G). 필요하면 말해줘 — 같은 포맷으로 원하는 만큼 뽑아줄게.
- 생성 스크립트: `scripts/gen_afe_input_csv.py`.
