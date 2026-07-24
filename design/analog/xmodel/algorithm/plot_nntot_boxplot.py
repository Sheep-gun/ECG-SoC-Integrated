# plot_nntot_boxplot.py
# NNTot feature를 class별 boxplot으로 확인하는 코드

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# 설정
# =========================================================
CSV_PATH = Path("ecg_extended_features_revised.csv")
OUT_DIR = Path("nntot_boxplot_result")

OUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# CSV 로드
# =========================================================
df = pd.read_csv(CSV_PATH)

if "Class" not in df.columns:
    raise ValueError("CSV 파일에 'Class' column이 없습니다.")

if "NNTot" not in df.columns:
    raise ValueError("CSV 파일에 'NNTot' column이 없습니다.")


# =========================================================
# Class별 NNTot 요약 통계 저장
# =========================================================
summary_df = (
    df.groupby("Class")["NNTot"]
    .agg(
        total_records="size",
        valid_count="count",
        missing_count=lambda x: x.isna().sum(),
        mean="mean",
        std="std",
        median="median",
        min="min",
        max="max",
    )
    .reset_index()
)

summary_df["missing_rate_percent"] = (
    summary_df["missing_count"] / summary_df["total_records"] * 100
)

summary_path = OUT_DIR / "nntot_summary_by_class.csv"
summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")


# =========================================================
# NNTot boxplot 생성
# NaN만 있는 class는 boxplot에서 제외됨
# =========================================================
classes = sorted(df["Class"].dropna().unique())

valid_classes = []
values_by_class = []

for cls in classes:
    values = df.loc[df["Class"] == cls, "NNTot"].dropna().values

    if len(values) > 0:
        valid_classes.append(cls)
        values_by_class.append(values)

if len(valid_classes) == 0:
    raise ValueError("NNTot 유효값이 있는 class가 없습니다.")

plt.figure(figsize=(8, 5))

try:
    plt.boxplot(
        values_by_class,
        tick_labels=valid_classes,
        showmeans=True
    )
except TypeError:
    # matplotlib 구버전 호환
    plt.boxplot(
        values_by_class,
        labels=valid_classes,
        showmeans=True
    )

plt.title("NNTot by ECG Class")
plt.xlabel("Class")
plt.ylabel("NNTot")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

boxplot_path = OUT_DIR / "nntot_boxplot.png"
plt.savefig(boxplot_path, dpi=180)
plt.close()


# =========================================================
# Missing rate plot 생성
# AFF처럼 NNTot가 전부 NaN인 class 확인용
# =========================================================
plt.figure(figsize=(8, 5))
plt.bar(summary_df["Class"], summary_df["missing_rate_percent"])
plt.title("NNTot Missing Rate by ECG Class")
plt.xlabel("Class")
plt.ylabel("Missing Rate (%)")
plt.ylim(0, 100)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

missing_plot_path = OUT_DIR / "nntot_missing_rate.png"
plt.savefig(missing_plot_path, dpi=180)
plt.close()


# =========================================================
# 결과 출력
# =========================================================
print("\n==============================")
print("NNTot Boxplot 생성 완료")
print("==============================")
print(f"입력 CSV: {CSV_PATH}")
print(f"저장 폴더: {OUT_DIR}")
print(f"NNTot boxplot: {boxplot_path}")
print(f"NNTot missing rate plot: {missing_plot_path}")
print(f"NNTot summary CSV: {summary_path}")

print("\n[NNTot summary by class]")
print(summary_df.to_string(index=False))

print("\n[주의]")
print("NNTot가 전부 NaN인 class는 boxplot에 표시되지 않습니다.")
print("예를 들어 AFF class의 NNTot가 모두 NaN이면 boxplot에는 ARR/CHF/NSR만 표시됩니다.")