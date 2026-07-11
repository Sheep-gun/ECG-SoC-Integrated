from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd
import wfdb
import neurokit2 as nk


# =========================================================
# 설정
# =========================================================
BASE_PATH = Path("./physionet.org/files")
SAVE_FEATURE_FILENAME = "ecg_extended_features_revised.csv"
SAVE_SUMMARY_FILENAME = "ecg_feature_summary_by_class.csv"

CLASS_MAPPING = {
    "afdb": "AFF",
    "chfdb": "CHF",
    "mitdb": "ARR",
    "nsrdb": "NSR",
}

CANDIDATE_ANN_EXTS = ("atr", "ecg", "qrs", "qrsc")

# 모든 레코드를 동일하게 앞 5분만 분석
ANALYSIS_SECONDS = 300

# 사용할 lead
LEAD_INDEX = 0

# 프로젝트 SoC는 1kSPS를 목표로 하지만, 원본 데이터의 샘플링 정보를 보존하는 것이
# 특징 비교에는 더 안전하다. 하드웨어 입력 조건과 맞추고 싶으면 1000으로 변경.
RESAMPLE_TO_HZ: Optional[int] = None

# 생리적으로 너무 이상한 interval 제거용 범위(ms)
RR_MIN_MS = 250
RR_MAX_MS = 2500

PP_MIN_MS = 250
PP_MAX_MS = 2500

RT_MIN_MS = 50
RT_MAX_MS = 500

ST_MIN_MS = 20
ST_MAX_MS = 500

QT_MIN_MS = 150
QT_MAX_MS = 700

R_TO_TOFF_MIN_MS = 80
R_TO_TOFF_MAX_MS = 700

S_TO_TOFF_MIN_MS = 50
S_TO_TOFF_MAX_MS = 700

QRS_MIN_MS = 40
QRS_MAX_MS = 220

ST_SEG_MIN_MS = 20
ST_SEG_MAX_MS = 300

# MIT-BIH 계열 annotation에서 beat로 취급할 수 있는 대표 symbol
# DB마다 annotation 체계가 조금 다를 수 있으므로, annotation 기반 값은 보조 지표로만 사용.
BEAT_SYMBOLS = set("NLRBAaJSEj/VFfeQ")
NORMAL_BEAT_SYMBOLS = {"N"}


# =========================================================
# 유틸 함수
# =========================================================
def find_dat_files(base_path: Path) -> list[Path]:
    dat_files = []

    for path in base_path.rglob("*.dat"):
        if not any(part in CLASS_MAPPING for part in path.parts):
            continue

        patient_id = path.stem

        # 중복/파생 record 제거
        if patient_id.startswith("x_"):
            continue

        dat_files.append(path)

    return sorted(dat_files)


def infer_db_folder(file_path: Path) -> Optional[str]:
    for part in file_path.parts:
        if part in CLASS_MAPPING:
            return part
    return None


def find_annotation_ext(record_base: Path) -> Optional[str]:
    for ext in CANDIDATE_ANN_EXTS:
        ann_path = Path(str(record_base) + f".{ext}")
        if ann_path.exists():
            return ext
    return None


def get_ecg_signal(record, lead_index: int = 0) -> np.ndarray:
    if getattr(record, "n_sig", 0) <= lead_index:
        raise ValueError(
            f"lead_index={lead_index} 사용 불가. 현재 신호 개수={getattr(record, 'n_sig', 0)}"
        )

    if getattr(record, "p_signal", None) is not None:
        sig = record.p_signal[:, lead_index]
    elif getattr(record, "d_signal", None) is not None:
        # d_signal만 있는 경우 adc count일 수 있으므로 절대 전압 특징 해석에 주의 필요
        sig = record.d_signal[:, lead_index].astype(float)
    else:
        raise ValueError("record에서 p_signal/d_signal을 찾지 못했습니다.")

    return np.asarray(sig, dtype=np.float64)


def maybe_resample_signal(signal: np.ndarray, fs: float) -> Tuple[np.ndarray, float]:
    if RESAMPLE_TO_HZ is None or int(fs) == int(RESAMPLE_TO_HZ):
        return signal, fs

    target_fs = float(RESAMPLE_TO_HZ)
    desired_length = int(round(len(signal) * target_fs / fs))
    if desired_length < 2:
        return signal, fs

    resampled = nk.signal_resample(
        signal,
        sampling_rate=fs,
        desired_sampling_rate=target_fs,
        method="interpolation",
    )
    return np.asarray(resampled, dtype=np.float64), target_fs


def to_float_array(values: Optional[Iterable]) -> np.ndarray:
    if values is None:
        return np.array([], dtype=float)

    arr = []
    for v in values:
        if v is None:
            arr.append(np.nan)
        else:
            try:
                arr.append(float(v))
            except Exception:
                arr.append(np.nan)

    return np.asarray(arr, dtype=float)


def clean_peak_array(arr: Iterable) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return arr
    arr = np.unique(arr.astype(np.int64))
    return arr.astype(float)


def valid_array(arr: Iterable) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    return arr[np.isfinite(arr)]


def diff_intervals_ms(peaks: Iterable, fs: float, min_ms=None, max_ms=None) -> np.ndarray:
    peaks = clean_peak_array(peaks)
    if len(peaks) < 2:
        return np.array([], dtype=float)

    intervals = np.diff(peaks) / fs * 1000.0

    mask = np.isfinite(intervals)
    if min_ms is not None:
        mask &= intervals >= min_ms
    if max_ms is not None:
        mask &= intervals <= max_ms

    return intervals[mask]


def pair_next_intervals_ms(starts: Iterable, ends: Iterable, fs: float, min_ms=None, max_ms=None) -> np.ndarray:
    """
    starts의 각 점에 대해, 그 이후에 나오는 첫 번째 ends를 1:1로 매칭.
    missing point가 있어도 비교적 안전하게 interval을 계산하기 위한 함수.
    """
    starts = clean_peak_array(starts)
    ends = clean_peak_array(ends)

    if len(starts) == 0 or len(ends) == 0:
        return np.array([], dtype=float)

    out = []
    j = 0

    for s in starts:
        while j < len(ends) and ends[j] <= s:
            j += 1

        if j >= len(ends):
            break

        delta_ms = (ends[j] - s) / fs * 1000.0

        ok = True
        if min_ms is not None and delta_ms < min_ms:
            ok = False
        if max_ms is not None and delta_ms > max_ms:
            ok = False

        if ok:
            out.append(delta_ms)
            j += 1

    return np.asarray(out, dtype=float)


def filter_range(arr: Iterable, min_value=None, max_value=None) -> np.ndarray:
    arr = valid_array(arr)
    if arr.size == 0:
        return arr
    mask = np.ones(arr.shape, dtype=bool)
    if min_value is not None:
        mask &= arr >= min_value
    if max_value is not None:
        mask &= arr <= max_value
    return arr[mask]


def safe_count(arr: Iterable) -> int:
    return int(len(valid_array(arr)))


def safe_mean(arr: Iterable) -> float:
    arr = valid_array(arr)
    if len(arr) == 0:
        return np.nan
    return round(float(np.mean(arr)), 2)


def safe_median(arr: Iterable) -> float:
    arr = valid_array(arr)
    if len(arr) == 0:
        return np.nan
    return round(float(np.median(arr)), 2)


def safe_std(arr: Iterable) -> float:
    arr = valid_array(arr)
    if len(arr) < 2:
        return np.nan
    return round(float(np.std(arr, ddof=1)), 2)


def safe_min(arr: Iterable) -> float:
    arr = valid_array(arr)
    if len(arr) == 0:
        return np.nan
    return round(float(np.min(arr)), 2)


def safe_max(arr: Iterable) -> float:
    arr = valid_array(arr)
    if len(arr) == 0:
        return np.nan
    return round(float(np.max(arr)), 2)


def safe_iqr(arr: Iterable) -> float:
    arr = valid_array(arr)
    if len(arr) < 2:
        return np.nan
    q75, q25 = np.percentile(arr, [75, 25])
    return round(float(q75 - q25), 2)


def safe_cv(arr: Iterable) -> float:
    arr = valid_array(arr)
    if len(arr) < 2:
        return np.nan
    mean = np.mean(arr)
    if np.isclose(mean, 0.0):
        return np.nan
    return round(float(np.std(arr, ddof=1) / mean), 4)


def safe_percentile(arr: Iterable, q: float) -> float:
    arr = valid_array(arr)
    if len(arr) == 0:
        return np.nan
    return round(float(np.percentile(arr, q)), 2)


def compute_rmssd(rr_ms: Iterable) -> float:
    rr_ms = valid_array(rr_ms)
    if len(rr_ms) < 2:
        return np.nan

    diff_rr = np.diff(rr_ms)
    if len(diff_rr) == 0:
        return np.nan

    rmssd = np.sqrt(np.mean(diff_rr ** 2))
    return round(float(rmssd), 2)


def compute_pnn50(rr_ms: Iterable) -> float:
    rr_ms = valid_array(rr_ms)
    if len(rr_ms) < 2:
        return np.nan

    diff_rr = np.abs(np.diff(rr_ms))
    if len(diff_rr) == 0:
        return np.nan

    pnn50 = np.mean(diff_rr > 50.0) * 100.0
    return round(float(pnn50), 2)


def compute_qtc(qt_ms: Iterable, rr_ms: Iterable) -> Tuple[float, float]:
    """
    QTc 계산.
    Bazett: QT / sqrt(RR)
    Fridericia: QT / cbrt(RR)
    단위: QT, RR는 ms로 들어오고 QTc도 ms로 반환.
    """
    qt_ms = valid_array(qt_ms)
    rr_ms = valid_array(rr_ms)
    n = min(len(qt_ms), len(rr_ms))
    if n == 0:
        return np.nan, np.nan

    qt_sec = qt_ms[:n] / 1000.0
    rr_sec = rr_ms[:n] / 1000.0
    rr_sec = rr_sec[rr_sec > 0]
    qt_sec = qt_sec[: len(rr_sec)]

    if len(rr_sec) == 0:
        return np.nan, np.nan

    qtc_bazett = qt_sec / np.sqrt(rr_sec) * 1000.0
    qtc_fridericia = qt_sec / np.cbrt(rr_sec) * 1000.0
    return safe_mean(qtc_bazett), safe_mean(qtc_fridericia)


def extract_annotation_features(annotation, max_sample: Optional[int] = None) -> Dict[str, float]:
    """
    annotation 기반 beat count 특징.
    annotation이 없는 DB도 있으므로 전체 파이프라인이 멈추지 않게 모두 NaN 처리 가능하게 구성.
    """
    features = {
        "NNTot": np.nan,
        "AnnBeatTot": np.nan,
        "NormalBeat_Count": np.nan,
        "AbnormalBeat_Count": np.nan,
        "NormalBeat_Ratio": np.nan,
        "AbnormalBeat_Ratio": np.nan,
    }

    if annotation is None:
        return features

    beat_samples = []
    normal_count = 0
    abnormal_count = 0

    for sample, symbol in zip(annotation.sample, annotation.symbol):
        if max_sample is not None and sample >= max_sample:
            break

        if symbol in BEAT_SYMBOLS:
            beat_samples.append(sample)
            if symbol in NORMAL_BEAT_SYMBOLS:
                normal_count += 1
            else:
                abnormal_count += 1

    beat_samples = np.asarray(beat_samples, dtype=np.int64)
    beat_count = len(beat_samples)

    features["AnnBeatTot"] = float(beat_count) if beat_count > 0 else np.nan
    features["NormalBeat_Count"] = float(normal_count) if beat_count > 0 else np.nan
    features["AbnormalBeat_Count"] = float(abnormal_count) if beat_count > 0 else np.nan

    if beat_count > 0:
        features["NormalBeat_Ratio"] = round(float(normal_count / beat_count), 4)
        features["AbnormalBeat_Ratio"] = round(float(abnormal_count / beat_count), 4)

    # 기존 코드의 의미를 유지: 정상 beat N 사이 interval 개수
    # normal_count가 k개이면 정상 NN interval은 k-1개.
    if normal_count >= 2:
        features["NNTot"] = float(normal_count - 1)

    return features


def default_feature_dict() -> Dict[str, float]:
    return {
        # record/meta
        "Original_FS": np.nan,
        "Used_FS": np.nan,
        "RPeak_Count": np.nan,
        "Delineation_OK": 0.0,
        "Valid_RR_Count": np.nan,
        "RR_Valid_Ratio": np.nan,

        # 기존 특징
        "RTdis": np.nan,
        "IBIM": np.nan,
        "STdis": np.nan,
        "QTdis": np.nan,
        "PPmean": np.nan,
        "RRTot": np.nan,
        "RTotfrdis": np.nan,
        "STotfrdis": np.nan,
        "IBISD": np.nan,
        "RMSSD": np.nan,
        "pNN50": np.nan,

        # RR 변동성/이상치: AFF/ARR 구분에 중요
        "HR_Mean": np.nan,
        "HR_Std": np.nan,
        "RR_Median": np.nan,
        "RR_Min": np.nan,
        "RR_Max": np.nan,
        "RR_Range": np.nan,
        "RR_IQR": np.nan,
        "RR_CV": np.nan,
        "RR_DiffMean": np.nan,
        "RR_DiffStd": np.nan,
        "RR_OutlierRatio_20pct": np.nan,

        # QRS 폭/형태: CHF 판별에 중요
        "QRS_Width_Mean": np.nan,
        "QRS_Width_Std": np.nan,
        "QRS_Width_Median": np.nan,
        "QRS_Width_Max": np.nan,
        "QRS_WideRatio_120ms": np.nan,
        "STseg_Mean": np.nan,

        # QT 보정
        "QTc_Bazett": np.nan,
        "QTc_Fridericia": np.nan,

        # 전압/진폭 관련: CHF의 전반적 전압 감소 후보 특징
        # 단, DB/lead 차이에 민감하므로 해석 시 주의.
        "Signal_Mean": np.nan,
        "Signal_Std": np.nan,
        "Signal_RMS": np.nan,
        "Signal_PeakToPeak": np.nan,
        "R_Amp_Mean": np.nan,
        "R_Amp_Std": np.nan,
        "QRS_Amp_Mean": np.nan,

        # slope/delta: 프로젝트 spike encoder와 직접 연결되는 후보 특징
        "Delta_MeanAbs": np.nan,
        "Delta_Std": np.nan,
        "Delta_P95Abs": np.nan,
        "Delta_P99Abs": np.nan,
        "Delta_MaxAbs": np.nan,
        "Delta_SignChangeRate": np.nan,
    }


def extract_extended_features(ecg_signal: np.ndarray, fs: float, original_fs: Optional[float] = None) -> Dict[str, float]:
    """
    Signal + NeuroKit2 기반 feature 추출.
    프로젝트 분류 근거인 RR interval/variance, QRS width, slope/delta를 강화한 버전.
    """
    feature_dict = default_feature_dict()
    feature_dict["Original_FS"] = float(original_fs if original_fs is not None else fs)
    feature_dict["Used_FS"] = float(fs)

    if len(ecg_signal) < int(fs * 2):
        return feature_dict

    # 결측/무한값 방어
    ecg_signal = np.asarray(ecg_signal, dtype=np.float64)
    ecg_signal = np.nan_to_num(ecg_signal, nan=np.nanmedian(ecg_signal), posinf=0.0, neginf=0.0)

    # NeuroKit 기본 ECG clean: baseline wander, powerline noise 등을 완화
    ecg_cleaned = nk.ecg_clean(ecg_signal, sampling_rate=fs)

    # -----------------------------------------------------
    # 신호 amplitude 및 delta/slope 후보 특징
    # -----------------------------------------------------
    feature_dict["Signal_Mean"] = safe_mean(ecg_cleaned)
    feature_dict["Signal_Std"] = safe_std(ecg_cleaned)
    feature_dict["Signal_RMS"] = safe_mean(np.sqrt(np.mean(ecg_cleaned ** 2)))
    feature_dict["Signal_PeakToPeak"] = safe_max(ecg_cleaned) - safe_min(ecg_cleaned)

    # delta = 현재값 - 이전값. fs가 다르면 delta scale이 달라지므로 fs를 곱해 slope 형태로 정규화.
    delta = np.diff(ecg_cleaned) * fs
    abs_delta = np.abs(delta)
    feature_dict["Delta_MeanAbs"] = safe_mean(abs_delta)
    feature_dict["Delta_Std"] = safe_std(delta)
    feature_dict["Delta_P95Abs"] = safe_percentile(abs_delta, 95)
    feature_dict["Delta_P99Abs"] = safe_percentile(abs_delta, 99)
    feature_dict["Delta_MaxAbs"] = safe_max(abs_delta)
    if len(delta) >= 2:
        feature_dict["Delta_SignChangeRate"] = round(float(np.mean(np.diff(np.sign(delta)) != 0)), 4)

    # -----------------------------------------------------
    # R-peak 검출 및 RR 기반 특징
    # -----------------------------------------------------
    try:
        _, rpeaks_info = nk.ecg_peaks(ecg_cleaned, sampling_rate=fs)
    except Exception:
        return feature_dict

    r_peaks = to_float_array(rpeaks_info.get("ECG_R_Peaks", []))
    r_peaks = clean_peak_array(r_peaks)
    feature_dict["RPeak_Count"] = float(len(r_peaks))

    rr_raw_ms = diff_intervals_ms(r_peaks, fs, None, None)
    rr_ms = diff_intervals_ms(r_peaks, fs, RR_MIN_MS, RR_MAX_MS)

    feature_dict["Valid_RR_Count"] = float(len(rr_ms)) if len(rr_ms) > 0 else np.nan
    feature_dict["RR_Valid_Ratio"] = round(float(len(rr_ms) / len(rr_raw_ms)), 4) if len(rr_raw_ms) > 0 else np.nan

    feature_dict["IBIM"] = safe_mean(rr_ms)
    feature_dict["IBISD"] = safe_std(rr_ms)
    feature_dict["RRTot"] = float(safe_count(rr_ms)) if len(rr_ms) > 0 else np.nan
    feature_dict["RMSSD"] = compute_rmssd(rr_ms)
    feature_dict["pNN50"] = compute_pnn50(rr_ms)

    if len(rr_ms) > 0:
        hr = 60000.0 / rr_ms
        feature_dict["HR_Mean"] = safe_mean(hr)
        feature_dict["HR_Std"] = safe_std(hr)
        feature_dict["RR_Median"] = safe_median(rr_ms)
        feature_dict["RR_Min"] = safe_min(rr_ms)
        feature_dict["RR_Max"] = safe_max(rr_ms)
        feature_dict["RR_Range"] = round(float(np.max(rr_ms) - np.min(rr_ms)), 2)
        feature_dict["RR_IQR"] = safe_iqr(rr_ms)
        feature_dict["RR_CV"] = safe_cv(rr_ms)

    if len(rr_ms) >= 2:
        rr_diff = np.abs(np.diff(rr_ms))
        feature_dict["RR_DiffMean"] = safe_mean(rr_diff)
        feature_dict["RR_DiffStd"] = safe_std(rr_diff)

        rr_median = np.median(rr_ms)
        if rr_median > 0:
            # 중앙 RR 대비 ±20% 이상 벗어난 interval 비율: ARR/AFF 후보 특징
            outlier_ratio = np.mean(np.abs(rr_ms - rr_median) > 0.2 * rr_median)
            feature_dict["RR_OutlierRatio_20pct"] = round(float(outlier_ratio), 4)

    if len(r_peaks) == 0:
        return feature_dict

    # R amplitude
    r_idx = r_peaks.astype(int)
    r_idx = r_idx[(r_idx >= 0) & (r_idx < len(ecg_cleaned))]
    if len(r_idx) > 0:
        r_amp = ecg_cleaned[r_idx]
        feature_dict["R_Amp_Mean"] = safe_mean(r_amp)
        feature_dict["R_Amp_Std"] = safe_std(r_amp)

    # -----------------------------------------------------
    # ECG delineation: P/Q/S/T 및 QRS/QT/ST 특징
    # -----------------------------------------------------
    try:
        _, waves = nk.ecg_delineate(
            ecg_cleaned,
            rpeaks=r_peaks.astype(int),
            sampling_rate=fs,
            method="dwt",
        )
        feature_dict["Delineation_OK"] = 1.0
    except Exception:
        return feature_dict

    p_peaks = to_float_array(waves.get("ECG_P_Peaks", []))
    q_peaks = to_float_array(waves.get("ECG_Q_Peaks", []))
    s_peaks = to_float_array(waves.get("ECG_S_Peaks", []))
    t_peaks = to_float_array(waves.get("ECG_T_Peaks", []))
    t_offsets = to_float_array(waves.get("ECG_T_Offsets", []))
    t_onsets = to_float_array(waves.get("ECG_T_Onsets", []))
    r_onsets = to_float_array(waves.get("ECG_R_Onsets", []))
    r_offsets = to_float_array(waves.get("ECG_R_Offsets", []))

    # PPmean = mean P-P interval
    pp_ms = diff_intervals_ms(p_peaks, fs, PP_MIN_MS, PP_MAX_MS)
    feature_dict["PPmean"] = safe_mean(pp_ms)

    # RTdis = R peak -> T peak
    rt_ms = pair_next_intervals_ms(r_peaks, t_peaks, fs, min_ms=RT_MIN_MS, max_ms=RT_MAX_MS)
    feature_dict["RTdis"] = safe_mean(rt_ms)

    # STdis = S peak -> T peak
    st_ms = pair_next_intervals_ms(s_peaks, t_peaks, fs, min_ms=ST_MIN_MS, max_ms=ST_MAX_MS)
    feature_dict["STdis"] = safe_mean(st_ms)

    # QTdis: QRS onset에 가까운 R onset -> T offset, 없으면 Q peak -> T offset
    if len(clean_peak_array(r_onsets)) > 0:
        qt_ms = pair_next_intervals_ms(r_onsets, t_offsets, fs, min_ms=QT_MIN_MS, max_ms=QT_MAX_MS)
    else:
        qt_ms = pair_next_intervals_ms(q_peaks, t_offsets, fs, min_ms=QT_MIN_MS, max_ms=QT_MAX_MS)
    feature_dict["QTdis"] = safe_mean(qt_ms)

    qtc_bazett, qtc_fridericia = compute_qtc(qt_ms, rr_ms)
    feature_dict["QTc_Bazett"] = qtc_bazett
    feature_dict["QTc_Fridericia"] = qtc_fridericia

    # RTotfrdis = R peak -> T offset
    r_to_toff_ms = pair_next_intervals_ms(
        r_peaks,
        t_offsets,
        fs,
        min_ms=R_TO_TOFF_MIN_MS,
        max_ms=R_TO_TOFF_MAX_MS,
    )
    feature_dict["RTotfrdis"] = safe_mean(r_to_toff_ms)

    # STotfrdis = S peak -> T offset
    s_to_toff_ms = pair_next_intervals_ms(
        s_peaks,
        t_offsets,
        fs,
        min_ms=S_TO_TOFF_MIN_MS,
        max_ms=S_TO_TOFF_MAX_MS,
    )
    feature_dict["STotfrdis"] = safe_mean(s_to_toff_ms)

    # QRS width: R onset -> R offset. 없으면 Q peak -> S peak로 근사.
    qrs_width_ms = pair_next_intervals_ms(
        r_onsets,
        r_offsets,
        fs,
        min_ms=QRS_MIN_MS,
        max_ms=QRS_MAX_MS,
    )
    if len(qrs_width_ms) == 0:
        qrs_width_ms = pair_next_intervals_ms(
            q_peaks,
            s_peaks,
            fs,
            min_ms=QRS_MIN_MS,
            max_ms=QRS_MAX_MS,
        )

    feature_dict["QRS_Width_Mean"] = safe_mean(qrs_width_ms)
    feature_dict["QRS_Width_Std"] = safe_std(qrs_width_ms)
    feature_dict["QRS_Width_Median"] = safe_median(qrs_width_ms)
    feature_dict["QRS_Width_Max"] = safe_max(qrs_width_ms)
    if len(qrs_width_ms) > 0:
        feature_dict["QRS_WideRatio_120ms"] = round(float(np.mean(qrs_width_ms >= 120.0)), 4)

    # ST segment: QRS offset -> T onset
    st_seg_ms = pair_next_intervals_ms(
        r_offsets,
        t_onsets,
        fs,
        min_ms=ST_SEG_MIN_MS,
        max_ms=ST_SEG_MAX_MS,
    )
    feature_dict["STseg_Mean"] = safe_mean(st_seg_ms)

    # QRS amplitude 근사: R amplitude - min(Q/S amplitude)
    q_idx = clean_peak_array(q_peaks).astype(int)
    s_idx = clean_peak_array(s_peaks).astype(int)
    n_amp = min(len(r_idx), len(q_idx), len(s_idx))
    qrs_amp = []
    for k in range(n_amp):
        qi, ri, si = q_idx[k], r_idx[k], s_idx[k]
        if 0 <= qi < len(ecg_cleaned) and 0 <= ri < len(ecg_cleaned) and 0 <= si < len(ecg_cleaned):
            baseline_val = min(ecg_cleaned[qi], ecg_cleaned[si])
            qrs_amp.append(ecg_cleaned[ri] - baseline_val)
    feature_dict["QRS_Amp_Mean"] = safe_mean(qrs_amp)

    return feature_dict


def make_class_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    증상별 특징 차이를 빠르게 보기 위한 요약 테이블 생성.
    각 feature마다 class별 count/mean/std/median/min/max를 저장.
    """
    meta_cols = {"Patient_ID", "Class", "DB", "Record_Path", "Used_seconds", "Annotation_Ext"}
    numeric_cols = [col for col in df.columns if col not in meta_cols and pd.api.types.is_numeric_dtype(df[col])]

    summary = (
        df.groupby("Class")[numeric_cols]
        .agg(["count", "mean", "std", "median", "min", "max"])
        .round(4)
    )

    # MultiIndex column을 CSV에서 보기 편하게 평탄화
    summary.columns = [f"{feature}_{stat}" for feature, stat in summary.columns]
    return summary.reset_index()


# =========================================================
# 메인
# =========================================================
def main() -> None:
    dat_files = find_dat_files(BASE_PATH)
    results = []

    print(f"총 {len(dat_files)}개의 dat 파일을 찾았습니다.\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for idx, file_path in enumerate(dat_files, start=1):
        record_base = file_path.with_suffix("")
        patient_id = record_base.name

        db_folder = infer_db_folder(file_path)
        if db_folder is None:
            print(f"[{idx}/{len(dat_files)}] [UNKNOWN] {patient_id} -> DB 폴더 미확인, 건너뜀")
            skip_count += 1
            continue

        symptom_class = CLASS_MAPPING[db_folder]
        print(f"[{idx}/{len(dat_files)}] [{symptom_class}] {patient_id} 처리 중...")

        try:
            record = wfdb.rdrecord(str(record_base))
            original_fs = float(record.fs)
            full_signal = get_ecg_signal(record, LEAD_INDEX)

            max_samples = min(len(full_signal), int(original_fs * ANALYSIS_SECONDS))
            ecg_signal = full_signal[:max_samples]
            used_seconds = round(len(ecg_signal) / original_fs, 2)

            # annotation은 있으면 읽고, 없어도 signal 기반 feature는 추출
            annotation = None
            ann_ext = find_annotation_ext(record_base)
            if ann_ext is not None:
                try:
                    annotation = wfdb.rdann(str(record_base), ann_ext)
                except Exception as ann_error:
                    print(f"  -> ⚠️ annotation 읽기 실패: {ann_error}")
                    annotation = None
            else:
                print("  -> ⚠️ annotation 파일 없음. annotation 기반 feature는 NaN 처리")

            # 하드웨어 1kSPS 조건에 맞추려면 RESAMPLE_TO_HZ = 1000으로 설정
            ecg_signal_used, used_fs = maybe_resample_signal(ecg_signal, original_fs)

            annotation_features = extract_annotation_features(annotation, max_sample=max_samples)
            signal_features = extract_extended_features(ecg_signal_used, used_fs, original_fs=original_fs)

            row = {
                "Patient_ID": patient_id,
                "Class": symptom_class,
                "DB": db_folder,
                "Record_Path": str(record_base),
                "Used_seconds": used_seconds,
                "Annotation_Ext": ann_ext if ann_ext is not None else "",
            }
            row.update(annotation_features)
            row.update(signal_features)
            results.append(row)

            success_count += 1

        except Exception as e:
            print(f"  -> ❌ 에러 발생: {e}")
            fail_count += 1

    df = pd.DataFrame(results)

    if not df.empty:
        front_cols = [
            "Patient_ID",
            "Class",
            "DB",
            "Record_Path",
            "Used_seconds",
            "Annotation_Ext",
        ]
        remaining_cols = [col for col in df.columns if col not in front_cols]
        df = df[front_cols + remaining_cols]
        df = df.sort_values(by=["Class", "Patient_ID"]).reset_index(drop=True)

    df.to_csv(SAVE_FEATURE_FILENAME, index=False, encoding="utf-8-sig")

    if not df.empty and "Class" in df.columns:
        summary_df = make_class_summary(df)
        summary_df.to_csv(SAVE_SUMMARY_FILENAME, index=False, encoding="utf-8-sig")
    else:
        summary_df = pd.DataFrame()

    print("\n==============================")
    print("추출 완료")
    print(f"성공: {success_count}")
    print(f"건너뜀: {skip_count}")
    print(f"실패: {fail_count}")
    print(f"저장 파일: {SAVE_FEATURE_FILENAME}")
    if not summary_df.empty:
        print(f"증상별 요약 파일: {SAVE_SUMMARY_FILENAME}")
    print("==============================")


if __name__ == "__main__":
    main()
