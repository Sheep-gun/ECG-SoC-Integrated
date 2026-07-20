#!/usr/bin/env python3
"""Regenerate data-derived figures after the class-label normalization to AF.

The script reads only checked-in CSV sources. It does not alter classifier
parameters, predictions, confusion-matrix counts, or feature values.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.tree import DecisionTreeClassifier, plot_tree


ROOT = Path(__file__).resolve().parents[1]
ALGORITHM = ROOT / "components" / "afe_xmodel" / "algorithm"
FEATURE_GRAPHS = (
    ROOT
    / "components"
    / "afe_xmodel"
    / "docs"
    / "digital_design"
    / "Actual Project"
    / "model_s_feature_graphs"
)
CLASS_ORDER = ["AF", "ARR", "CHF", "NSR"]


def title_for(metric: str) -> str:
    return metric.replace("_", " ").replace("af ", "AF ").replace("qrs", "QRS")


def draw_boxplot(ax: plt.Axes, frame: pd.DataFrame, metric: str) -> None:
    values = [
        frame.loc[frame["label"] == label, metric].dropna().to_numpy()
        for label in CLASS_ORDER
    ]
    ax.boxplot(
        values,
        tick_labels=CLASS_ORDER,
        showmeans=True,
        meanprops={"marker": "^", "markerfacecolor": "#2fb344", "markeredgecolor": "#2fb344"},
        medianprops={"color": "#f28e2b", "linewidth": 2},
    )
    ax.grid(axis="y", alpha=0.28)
    ax.set_xlabel("Class")


def regenerate_model_s_feature_graphs() -> int:
    source = pd.read_csv(FEATURE_GRAPHS / "model_s_feature_plot_source_values.csv")
    manifest = pd.read_csv(FEATURE_GRAPHS / "model_s_feature_plot_manifest.csv")
    created = 0

    for scope, scope_rows in manifest.groupby("scope", sort=False):
        frame = source if scope == "all" else source.loc[source["split"] == scope]
        output_dir = FEATURE_GRAPHS / ("all_segments" if scope == "all" else "test_segments")
        output_dir.mkdir(parents=True, exist_ok=True)
        scope_title = "all segments" if scope == "all" else "strict test segments"

        overview_rows = scope_rows.loc[scope_rows["plot_type"] == "boxplot"].reset_index(drop=True)
        fig, axes = plt.subplots(4, 4, figsize=(20, 16))
        for ax, (_, row) in zip(axes.flat, overview_rows.iterrows()):
            metric = row["metric"]
            draw_boxplot(ax, frame, metric)
            ax.set_title(title_for(metric), fontsize=10, fontweight="bold")
            ax.set_ylabel(metric)
        for ax in axes.flat[len(overview_rows) :]:
            ax.axis("off")
        fig.suptitle(f"Model S feature distributions ({scope_title})", fontsize=20, fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        fig.savefig(output_dir / "model_s_feature_boxplot_overview.png", dpi=180)
        plt.close(fig)
        created += 1

        for _, row in scope_rows.iterrows():
            if row["plot_type"] == "overview":
                continue
            metric = row["metric"]
            fig, ax = plt.subplots(figsize=(10, 6))
            if row["plot_type"] == "boxplot":
                draw_boxplot(ax, frame, metric)
                ax.set_ylabel(metric)
            else:
                means = [frame.loc[frame["label"] == label, metric].mean() for label in CLASS_ORDER]
                ax.bar(CLASS_ORDER, means, color="#4c78a8")
                ax.set_xlabel("Class")
                ax.set_ylabel(f"Mean {metric}")
                ax.grid(axis="y", alpha=0.28)
            ax.set_title(f"{title_for(metric)} by Class ({scope_title})", fontsize=18, fontweight="bold")
            fig.tight_layout()
            fig.savefig(output_dir / Path(row["png"]).name, dpi=180)
            plt.close(fig)
            created += 1

    return created


def regenerate_legacy_algorithm_figures() -> int:
    frame = pd.read_csv(ALGORITHM / "ecg_extended_features_revised.csv")
    output_dir = ALGORITHM / "boxplot10rank"
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_files = [
        ("Delta_SignChangeRate", "boxplot_01_Delta_SignChangeRate.png"),
        ("R_Amp_Mean", "boxplot_02_R_Amp_Mean.png"),
        ("Delta_P99Abs", "boxplot_03_Delta_P99Abs.png"),
        ("Delta_MaxAbs", "boxplot_04_Delta_MaxAbs.png"),
        ("Delta_Std", "boxplot_05_Delta_Std.png"),
        ("QTdis", "boxplot_06_QTdis.png"),
        ("pNN50", "boxplot_07_pNN50.png"),
        ("QRS_Width_Mean", "boxplot_08_QRS_Width_Mean.png"),
        ("PPmean", "boxplot_09_PPmean.png"),
        ("QRS_WideRatio_120ms", "boxplot_10_QRS_WideRatio_120ms.png"),
    ]

    for index, (feature, filename) in enumerate(feature_files, start=1):
        values = [
            frame.loc[frame["Class"] == label, feature].dropna().to_numpy()
            for label in CLASS_ORDER
        ]
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.boxplot(values, tick_labels=CLASS_ORDER, showmeans=True)
        ax.set_title(f"Boxplot #{index}: {feature} by Class", fontsize=18)
        ax.set_xlabel("Class", fontsize=14)
        ax.set_ylabel(feature, fontsize=14)
        ax.grid(axis="y", alpha=0.28)
        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=180)
        plt.close(fig)

    excluded = {
        "Patient_ID", "Class", "DB", "Record_Path", "Used_seconds", "Annotation_Ext",
        "Original_FS", "Used_FS", "Delineation_OK", "NNTot", "AnnBeatTot",
        "NormalBeat_Count", "AbnormalBeat_Count", "NormalBeat_Ratio", "AbnormalBeat_Ratio",
        "RPeak_Count", "Valid_RR_Count", "RR_Valid_Ratio", "RRTot",
    }
    feature_columns = [
        column for column in frame.columns
        if column not in excluded and pd.api.types.is_numeric_dtype(frame[column])
    ]
    x = frame[feature_columns]
    y = frame["Class"]
    imputer = SimpleImputer(strategy="median")
    x_imputed = pd.DataFrame(imputer.fit_transform(x), columns=x.columns)
    tree = DecisionTreeClassifier(max_depth=4, random_state=42)
    tree.fit(x_imputed, y)
    fig, ax = plt.subplots(figsize=(20, 10))
    plot_tree(
        tree,
        feature_names=list(x.columns),
        class_names=list(tree.classes_),
        filled=True,
        rounded=True,
        fontsize=12,
        ax=ax,
    )
    ax.set_title("Decision Tree for ECG Classification (Threshold Rules)", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ALGORITHM / "decision_tree.png", dpi=150)
    plt.close(fig)
    return len(feature_files) + 1


def main() -> int:
    model_count = regenerate_model_s_feature_graphs()
    legacy_count = regenerate_legacy_algorithm_figures()
    print(f"regenerated {model_count + legacy_count} AF-labeled data figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
