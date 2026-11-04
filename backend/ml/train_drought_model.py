
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    BASE_DIR
    / "Data"
    / "Processed"
    / "gujarat_district_spi.csv"
)

MODEL_DIR = BASE_DIR / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "drought_rf_model.pkl"
METRICS_FILE = MODEL_DIR / "drought_model_metrics.json"


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(DATA_FILE)

required_columns = [
    "date",
    "district",
    "rainfall_mm",
    "spi_3",
]

missing = [
    column for column in required_columns
    if column not in df.columns
]

if missing:
    raise ValueError(f"Missing dataset columns: {missing}")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["rainfall_mm"] = pd.to_numeric(
    df["rainfall_mm"], errors="coerce"
)
df["spi_3"] = pd.to_numeric(
    df["spi_3"], errors="coerce"
)

df = df.dropna(
    subset=["date", "district", "rainfall_mm", "spi_3"]
)

df = df.sort_values(["district", "date"]).copy()


# --------------------------------------------------
# CREATE TARGET: NEXT MONTH'S DROUGHT CATEGORY
# --------------------------------------------------

def classify_drought(spi):
    if spi <= -2:
        return "Extreme Drought"
    elif spi <= -1.5:
        return "Severe Drought"
    elif spi <= -1:
        return "Moderate Drought"
    return "Normal"


df["target"] = (
    df.groupby("district")["spi_3"]
    .shift(-1)
    .apply(
        lambda value: (
            classify_drought(value)
            if pd.notna(value)
            else np.nan
        )
    )
)

# --------------------------------------------------
# FEATURE ENGINEERING
# --------------------------------------------------

grouped = df.groupby("district", group_keys=False)

df["rainfall_lag_1"] = grouped["rainfall_mm"].shift(1)
df["rainfall_lag_2"] = grouped["rainfall_mm"].shift(2)

df["rainfall_3m"] = (
    grouped["rainfall_mm"]
    .rolling(3)
    .sum()
    .reset_index(level=0, drop=True)
)

df["rainfall_6m"] = (
    grouped["rainfall_mm"]
    .rolling(6)
    .sum()
    .reset_index(level=0, drop=True)
)

df["spi_lag_1"] = grouped["spi_3"].shift(1)
df["spi_lag_2"] = grouped["spi_3"].shift(2)

df["month"] = df["date"].dt.month

FEATURES = [
    "rainfall_mm",
    "rainfall_lag_1",
    "rainfall_lag_2",
    "rainfall_3m",
    "rainfall_6m",
    "spi_3",
    "spi_lag_1",
    "spi_lag_2",
    "month",
]

df = df.dropna(subset=FEATURES + ["target"]).copy()

if df.empty:
    raise ValueError("No usable training rows after feature engineering.")


# --------------------------------------------------
# CHRONOLOGICAL TRAIN / TEST SPLIT
# --------------------------------------------------

df = df.sort_values("date")

split_date = df["date"].quantile(0.80)

train = df[df["date"] <= split_date].copy()
test = df[df["date"] > split_date].copy()

if train.empty or test.empty:
    raise ValueError("Insufficient data for chronological split.")

X_train = train[FEATURES]
y_train = train["target"]

X_test = test[FEATURES]
y_test = test["target"]


# --------------------------------------------------
# MODEL
# --------------------------------------------------

model = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    (
        "classifier",
        RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
    ),
])

model.fit(X_train, y_train)

predictions = model.predict(X_test)


# --------------------------------------------------
# EVALUATION
# --------------------------------------------------

accuracy = accuracy_score(y_test, predictions)

print("\n========== MODEL EVALUATION ==========")
print(f"Training records: {len(train)}")
print(f"Testing records: {len(test)}")
print(f"Chronological split date: {split_date.date()}")
print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        labels=[
            "Normal",
            "Moderate Drought",
            "Severe Drought",
            "Extreme Drought",
        ],
        zero_division=0,
    )
)

print("\nConfusion Matrix:")
print(
    confusion_matrix(
        y_test,
        predictions,
        labels=[
            "Normal",
            "Moderate Drought",
            "Severe Drought",
            "Extreme Drought",
        ],
    )
)


# --------------------------------------------------
# SAVE MODEL AND METRICS
# --------------------------------------------------

joblib.dump(
    {
        "model": model,
        "features": FEATURES,
        "target_classes": list(model.classes_),
    },
    MODEL_FILE,
)

import json

metrics = {
    "accuracy": float(accuracy),
    "training_records": int(len(train)),
    "testing_records": int(len(test)),
    "split_date": str(split_date.date()),
    "features": FEATURES,
    "classes": list(model.classes_),
}

with open(METRICS_FILE, "w") as file:
    json.dump(metrics, file, indent=4)

print("\nModel saved:", MODEL_FILE)
print("Metrics saved:", METRICS_FILE)
