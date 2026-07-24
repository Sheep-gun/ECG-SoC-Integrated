# analyze_ecg_parameters.py
# ECG feature CSV를 이용해서
# 1) 증상별로 어떤 feature가 잘 구분되는지 ranking
# 2) 증상별 추천 파라미터
# 3) boxplot 생성
# 4) decision tree 생성
# 을 자동으로 수행하는 코드

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree


# =========================================================
# 설정
# =========================================================

DEFAULT_EXCLUDE_COLS = {
    # 식별자 / 라벨
    "Patient_ID",
    "Class",
    "DB",
    "Record_Path",

    # 분석 메타데이터
    "Used_seconds",
    "Annotation_Ext",
    "Original_FS",
    "Used_FS",
    "Delineation_OK",

    # annotation 기반 값 또는 count성 값
    # 너무 직접적인 라벨 정보가 될 수 있거나, record 길이 영향이 커서 제외
    "NNTot",
    "AnnBeatTot",
    "NormalBeat_Count",
    "AbnormalBeat_Count",
    "NormalBeat_Ratio",
    "AbnormalBeat_Ratio",

    # R peak 검출 품질/개수 관련
    "RPeak_Count",
    "Valid_RR_Count",
    "RR_Valid_Ratio",
    "RRTot",
}


# =========================================================
# 유틸 함수
# =========================================================

def make_output_dirs(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    boxplot_dir = out_dir / "boxplots"
    boxplot_dir.mkdir(parents=True, exist_ok=True)

    return boxplot_dir


def get_numeric_features(df: pd.DataFrame, label_col: str, exclude_cols: set):
    exclude_cols = set(exclude_cols)
    exclude_cols.add(label_col)

    features = []

    for col in df.columns:
        if col in exclude_cols:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            valid_count = df[col].notna().sum()

            # 유효값이 너무 적은 feature는 제외
            if valid_count >= 3:
                features.append(col)

    return features


def eta_squared_oneway(df: pd.DataFrame, feature: str, label_col: str):
    """
    클래스별 분산 차이를 보는 간단한 effect size.
    값이 클수록 class 간 분포 차이가 큼.

    eta^2 = between-group sum of squares / total sum of squares
    """
    temp = df[[feature, label_col]].dropna()

    if temp[label_col].nunique() < 2:
        return np.nan

    values = temp[feature].values.astype(float)
    grand_mean = np.mean(values)

    total_ss = np.sum((values - grand_mean) ** 2)

    if total_ss == 0:
        return 0.0

    between_ss = 0.0

    for cls, group in temp.groupby(label_col):
        group_values = group[feature].values.astype(float)
        group_mean = np.mean(group_values)
        between_ss += len(group_values) * (group_mean - grand_mean) ** 2

    return float(between_ss / total_ss)


def build_overall_feature_ranking(df: pd.DataFrame, features, label_col: str):
    """
    전체 4개 class를 구분하는 데 유리한 feature ranking 생성
    """
    classes = sorted(df[label_col].dropna().unique())

    rows = []

    for feature in features:
        eta2 = eta_squared_oneway(df, feature, label_col)

        row = {
            "Feature": feature,
            "EtaSquared": eta2,
        }

        for cls in classes:
            cls_values = df.loc[df[label_col] == cls, feature].dropna()

            row[f"{cls}_count"] = len(cls_values)
            row[f"{cls}_mean"] = cls_values.mean()
            row[f"{cls}_median"] = cls_values.median()
            row[f"{cls}_std"] = cls_values.std(ddof=1)

        rows.append(row)

    ranking_df = pd.DataFrame(rows)
    ranking_df = ranking_df.sort_values("EtaSquared", ascending=False).reset_index(drop=True)
    ranking_df.insert(0, "Overall_Rank", np.arange(1, len(ranking_df) + 1))

    return ranking_df


def build_classwise_recommendation(df: pd.DataFrame, features, label_col: str):
    """
    각 증상 class를 나머지 class와 비교해서
    어떤 feature가 해당 class 판별에 유리한지 계산.

    기준:
    - one-vs-rest ROC AUC
    - AUC가 1에 가까울수록 해당 class에서 값이 높은 방향으로 구분됨
    - AUC가 0에 가까울수록 해당 class에서 값이 낮은 방향으로 구분됨
    - Separability = max(AUC, 1-AUC)
    """
    classes = sorted(df[label_col].dropna().unique())

    rows = []

    for target_cls in classes:
        y = (df[label_col] == target_cls).astype(int)

        for feature in features:
            x = df[feature].astype(float)

            mask = x.notna() & y.notna()

            if mask.sum() < 5:
                continue

            if y[mask].nunique() < 2:
                continue

            try:
                auc = roc_auc_score(y[mask], x[mask])
            except Exception:
                continue

            separability = max(auc, 1.0 - auc)
            direction = "higher" if auc >= 0.5 else "lower"

            class_values = df.loc[df[label_col] == target_cls, feature].dropna()
            other_values = df.loc[df[label_col] != target_cls, feature].dropna()

            rows.append({
                "Class": target_cls,
                "Feature": feature,
                "Direction_for_this_class": direction,
                "OneVsRest_AUC": auc,
                "Separability": separability,
                "Class_Mean": class_values.mean(),
                "Other_Mean": other_values.mean(),
                "Class_Median": class_values.median(),
                "Other_Median": other_values.median(),
            })

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    result = result.sort_values(
        ["Class", "Separability"],
        ascending=[True, False]
    ).reset_index(drop=True)

    result.insert(
        1,
        "Rank_in_Class",
        result.groupby("Class").cumcount() + 1
    )

    return result


def plot_top_boxplots(df: pd.DataFrame, ranking_df: pd.DataFrame, label_col: str,
                      boxplot_dir: Path, top_n: int):
    """
    상위 feature들에 대해 class별 boxplot 생성
    """
    classes = sorted(df[label_col].dropna().unique())
    top_features = ranking_df["Feature"].head(top_n).tolist()

    saved_files = []

    for idx, feature in enumerate(top_features, start=1):
        values_by_class = [
            df.loc[df[label_col] == cls, feature].dropna().values
            for cls in classes
        ]

        plt.figure(figsize=(8, 5))
        plt.boxplot(values_by_class, tick_labels=classes, showmeans=True)
        plt.title(f"Boxplot #{idx}: {feature} by Class")
        plt.xlabel("Class")
        plt.ylabel(feature)
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()

        save_path = boxplot_dir / f"boxplot_{idx:02d}_{feature}.png"
        plt.savefig(save_path, dpi=160)
        plt.close()

        saved_files.append(save_path)

    return saved_files


def train_decision_tree(df: pd.DataFrame, features, label_col: str,
                        out_dir: Path, max_depth: int):
    """
    Decision Tree 학습 + 이미지 저장 + rule text 저장 + feature importance 저장
    """
    X = df[features]
    y = df[label_col]

    tree = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42
    )

    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("tree", tree)
    ])

    class_counts = y.value_counts()
    min_class_count = int(class_counts.min())

    if min_class_count >= 2:
        n_splits = min(5, min_class_count)

        cv = StratifiedKFold(
            n_splits=n_splits,
            shuffle=True,
            random_state=42
        )

        cv_scores = cross_val_score(
            pipe,
            X,
            y,
            cv=cv,
            scoring="accuracy"
        )
    else:
        cv_scores = np.array([])

    pipe.fit(X, y)

    fitted_tree = pipe.named_steps["tree"]

    # -----------------------------
    # Decision tree 이미지 저장
    # -----------------------------
    tree_png_path = out_dir / "decision_tree.png"

    plt.figure(figsize=(24, 12))
    plot_tree(
        fitted_tree,
        feature_names=features,
        class_names=fitted_tree.classes_,
        filled=False,
        rounded=True,
        fontsize=8
    )
    plt.title("Decision Tree for ECG Class Parameters")
    plt.tight_layout()
    plt.savefig(tree_png_path, dpi=180)
    plt.close()

    # -----------------------------
    # Decision tree rule 저장
    # -----------------------------
    tree_rules = export_text(
        fitted_tree,
        feature_names=features,
        decimals=3
    )

    rule_path = out_dir / "decision_tree_rules.txt"
    rule_path.write_text(tree_rules, encoding="utf-8")

    # -----------------------------
    # Feature importance 저장
    # -----------------------------
    importance_df = pd.DataFrame({
        "Feature": features,
        "DecisionTree_Importance": fitted_tree.feature_importances_
    })

    importance_df = importance_df.sort_values(
        "DecisionTree_Importance",
        ascending=False
    ).reset_index(drop=True)

    importance_path = out_dir / "decision_tree_feature_importance.csv"
    importance_df.to_csv(importance_path, index=False, encoding="utf-8-sig")

    return {
        "model": pipe,
        "cv_scores": cv_scores,
        "tree_png_path": tree_png_path,
        "rule_path": rule_path,
        "importance_df": importance_df,
        "importance_path": importance_path,
    }


def print_summary(df, label_col, ranking_df, classwise_df, tree_result):
    print("\n==============================")
    print("ECG Feature Analysis Summary")
    print("==============================")

    print("\n[Class count]")
    print(df[label_col].value_counts().to_string())

    print("\n[Top overall features]")
    print(
        ranking_df[
            ["Overall_Rank", "Feature", "EtaSquared"]
        ].head(10).to_string(index=False)
    )

    if not classwise_df.empty:
        print("\n[Top class-wise recommended parameters]")
        for cls in sorted(classwise_df["Class"].unique()):
            print(f"\n--- {cls} ---")
            temp = classwise_df[classwise_df["Class"] == cls].head(5)
            print(
                temp[
                    [
                        "Rank_in_Class",
                        "Feature",
                        "Direction_for_this_class",
                        "Separability",
                        "Class_Median",
                        "Other_Median",
                    ]
                ].to_string(index=False)
            )

    cv_scores = tree_result["cv_scores"]

    print("\n[Decision Tree CV accuracy]")
    if len(cv_scores) > 0:
        print(f"scores = {np.round(cv_scores, 3)}")
        print(f"mean   = {cv_scores.mean():.3f}")
        print(f"std    = {cv_scores.std():.3f}")
    else:
        print("CV를 수행하기에 class별 데이터 수가 부족합니다.")

    print("\n[Decision Tree top features]")
    print(tree_result["importance_df"].head(10).to_string(index=False))

    print("\n==============================")
    print("완료")
    print("==============================")


# =========================================================
# 메인
# =========================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--csv",
        type=str,
        default="ecg_extended_features_revised.csv",
        help="입력 ECG feature CSV 파일 경로"
    )

    parser.add_argument(
        "--label_col",
        type=str,
        default="Class",
        help="class label column 이름"
    )

    parser.add_argument(
        "--out_dir",
        type=str,
        default="ecg_parameter_analysis_result",
        help="결과 저장 폴더"
    )

    parser.add_argument(
        "--top_n_boxplot",
        type=int,
        default=12,
        help="boxplot으로 저장할 상위 feature 개수"
    )

    parser.add_argument(
        "--tree_depth",
        type=int,
        default=4,
        help="Decision Tree 최대 깊이"
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    label_col = args.label_col
    out_dir = Path(args.out_dir)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    df = pd.read_csv(csv_path)

    if label_col not in df.columns:
        raise ValueError(f"CSV 안에 label column '{label_col}'이 없습니다.")

    boxplot_dir = make_output_dirs(out_dir)

    features = get_numeric_features(
        df=df,
        label_col=label_col,
        exclude_cols=DEFAULT_EXCLUDE_COLS
    )

    if len(features) == 0:
        raise ValueError("사용 가능한 numeric feature가 없습니다.")

    print(f"입력 CSV: {csv_path}")
    print(f"총 record 수: {len(df)}")
    print(f"사용 feature 수: {len(features)}")
    print(f"결과 저장 폴더: {out_dir}")

    # 1. 전체 feature ranking
    ranking_df = build_overall_feature_ranking(
        df=df,
        features=features,
        label_col=label_col
    )

    ranking_path = out_dir / "feature_ranking_overall.csv"
    ranking_df.to_csv(ranking_path, index=False, encoding="utf-8-sig")

    # 2. 증상별 추천 parameter
    classwise_df = build_classwise_recommendation(
        df=df,
        features=features,
        label_col=label_col
    )

    classwise_path = out_dir / "classwise_parameter_recommendations.csv"
    classwise_df.to_csv(classwise_path, index=False, encoding="utf-8-sig")

    # 3. Boxplot 저장
    boxplot_files = plot_top_boxplots(
        df=df,
        ranking_df=ranking_df,
        label_col=label_col,
        boxplot_dir=boxplot_dir,
        top_n=args.top_n_boxplot
    )

    # 4. Decision Tree
    tree_result = train_decision_tree(
        df=df,
        features=features,
        label_col=label_col,
        out_dir=out_dir,
        max_depth=args.tree_depth
    )

    # 5. 요약 출력
    print_summary(
        df=df,
        label_col=label_col,
        ranking_df=ranking_df,
        classwise_df=classwise_df,
        tree_result=tree_result
    )

    print("\n[Saved files]")
    print(f"- 전체 feature ranking: {ranking_path}")
    print(f"- 증상별 추천 parameter: {classwise_path}")
    print(f"- Decision Tree 이미지: {tree_result['tree_png_path']}")
    print(f"- Decision Tree 규칙 txt: {tree_result['rule_path']}")
    print(f"- Decision Tree feature importance: {tree_result['importance_path']}")
    print(f"- Boxplot 폴더: {boxplot_dir}")
    print(f"- Boxplot 개수: {len(boxplot_files)}")


if __name__ == "__main__":
    main()