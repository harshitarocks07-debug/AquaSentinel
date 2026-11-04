"""
AquaSentinel flood-warning model training.
Target: next-day rainfall above a district-specific 95th percentile.
This is an extreme-rainfall proxy, not verified flood occurrence.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, average_precision_score, classification_report,
    confusion_matrix, f1_score, precision_score, recall_score
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data" / "Processed" / "daily_rainfall" / "gujarat_district_flood_features.csv"
OUT = ROOT / "ml" / "models"
NUM = ["rainfall_mm", "rainfall_3d_mm", "rainfall_7d_mm", "rainfall_30d_mm", "month"]
CAT = ["district"]

def main():
    if not DATA.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA}")
    df = pd.read_csv(DATA)
    required = set(["district", "date", "rainfall_mm"] + NUM)
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["district"] = df["district"].astype(str).str.strip()
    df = df.dropna(subset=["district", "date", "rainfall_mm"])
    df = df.sort_values(["district", "date"]).reset_index(drop=True)

    g = df.groupby("district", sort=False)
    df["next_rainfall"] = g["rainfall_mm"].shift(-1)
    df["target_date"] = g["date"].shift(-1)
    df = df.loc[(df["target_date"] - df["date"]).dt.days.eq(1)].copy()

    dates = np.array(sorted(df["target_date"].unique()))
    train_end = pd.Timestamp(dates[int(len(dates) * 0.70)])
    val_end = pd.Timestamp(dates[int(len(dates) * 0.85)])
    train_rows = df["target_date"] <= train_end

    thresholds = df.loc[train_rows].groupby("district")["next_rainfall"].quantile(0.95).to_dict()
    df["district_threshold"] = df["district"].map(thresholds)
    df = df.dropna(subset=["district_threshold"])
    df["target"] = (df["next_rainfall"] > df["district_threshold"]).astype("int8")

    train = df["target_date"] <= train_end
    valid = (df["target_date"] > train_end) & (df["target_date"] <= val_end)
    test = df["target_date"] > val_end
    features = NUM + CAT
    X_train, y_train = df.loc[train, features], df.loc[train, "target"]
    X_val, y_val = df.loc[valid, features], df.loc[valid, "target"]
    X_test, y_test = df.loc[test, features], df.loc[test, "target"]

    print("Date splits:", train_end.date(), val_end.date())
    print("Class counts:", {
        "train": y_train.value_counts().sort_index().to_dict(),
        "validation": y_val.value_counts().sort_index().to_dict(),
        "test": y_test.value_counts().sort_index().to_dict()
    })
    if any(y.nunique() < 2 for y in (y_train, y_val, y_test)):
        raise ValueError("A time split has only one class; inspect data/date coverage.")

    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUM),
        ("district", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]), CAT)
    ])
    scale = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    model = Pipeline([
        ("prep", prep),
        ("xgb", XGBClassifier(
            n_estimators=350, max_depth=5, learning_rate=0.05,
            subsample=0.85, colsample_bytree=0.85, min_child_weight=5,
            reg_lambda=2, objective="binary:logistic", eval_metric="aucpr",
            tree_method="hist", scale_pos_weight=scale, random_state=42, n_jobs=-1
        ))
    ])

    print("Training XGBoost...")
    model.fit(X_train, y_train)

    val_prob = model.predict_proba(X_val)[:, 1]
    thresholds_to_try = np.arange(0.20, 0.81, 0.02)
    f1s = [f1_score(y_val, val_prob >= t, zero_division=0) for t in thresholds_to_try]
    decision_threshold = float(thresholds_to_try[int(np.argmax(f1s))])

    test_prob = model.predict_proba(X_test)[:, 1]
    test_pred = (test_prob >= decision_threshold).astype(int)
    metrics = {
        "model": "XGBoostClassifier",
        "target": "Next-day rainfall above district-specific training-period 95th percentile",
        "warning": "Extreme-rainfall proxy; not verified flood occurrence or flood probability.",
        "features": features,
        "train_end": str(train_end.date()),
        "validation_end": str(val_end.date()),
        "district_thresholds_mm": {k: float(v) for k, v in thresholds.items()},
        "decision_threshold": decision_threshold,
        "validation_best_f1": float(max(f1s)),
        "test_accuracy": float(accuracy_score(y_test, test_pred)),
        "test_precision": float(precision_score(y_test, test_pred, zero_division=0)),
        "test_recall": float(recall_score(y_test, test_pred, zero_division=0)),
        "test_f1": float(f1_score(y_test, test_pred, zero_division=0)),
        "test_pr_auc": float(average_precision_score(y_test, test_prob)),
        "classification_report": classification_report(y_test, test_pred, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, test_pred).tolist(),
        "train_records": int(len(y_train)),
        "validation_records": int(len(y_val)),
        "test_records": int(len(y_test))
    }
    OUT.mkdir(parents=True, exist_ok=True)
    model_path = OUT / "flood_xgb_model.joblib"
    metrics_path = OUT / "flood_model_metrics.json"
    joblib.dump(model, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=4), encoding="utf-8")
    print("\nTEST REPORT")
    print(classification_report(y_test, test_pred, zero_division=0))
    print("PR-AUC:", round(metrics["test_pr_auc"], 4))
    print("Decision threshold:", round(decision_threshold, 2))
    print("Saved:", model_path)
    print("Metrics:", metrics_path)

if __name__ == "__main__":
    main()
