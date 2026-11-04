
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# 1. PATHS
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
# 2. LOAD DATA
# --------------------------------------------------

print("Loading drought dataset...")

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_FILE}"
    )

df = pd.read_csv(DATA_FILE)

required_columns = [
    "date",
    "district",
    "rainfall_mm",
    "spi_3",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

df["date"] = pd.to_datetime(df["date"])

df["rainfall_mm"] = pd.to_numeric(
    df["rainfall_mm"], errors="coerce"
)

df["spi_3"] = pd.to_numeric(
    df["spi_3"], errors="coerce"
)

df = df.sort_values(
    ["district", "date"]
).reset_index(drop=True)

print("Total records:", len(df))
print("Districts:", df["district"].nunique())


# --------------------------------------------------
# 3. CREATE DROUGHT CLASSES
# --------------------------------------------------

def classify_drought(spi):
    if pd.isna(spi):
        return np.nan
    elif spi <= -2:
        return "Extreme Drought"
    elif spi <= -1.5:
        return "Severe Drought"
    elif spi <= -1:
        return "Moderate Drought"
    else:
        return "Normal"


df["drought_class"] = df["spi_3"].apply(
    classify_drought
)


# --------------------------------------------------
# 4. FEATURE ENGINEERING
# --------------------------------------------------

grouped = df.groupby("district", sort=False)

# Historical rainfall features
df["rainfall_lag_1"] = grouped["rainfall_mm"].shift(1)
df["rainfall_lag_2"] = grouped["rainfall_mm"].shift(2)

# Rolling rainfall totals
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

# Historical SPI features
df["spi_lag_1"] = grouped["spi_3"].shift(1)
df["spi_lag_2"] = grouped["spi_3"].shift(2)

df["month"] = df["date"].dt.month

# Target: next month's SPI-derived drought category
df["target"] = (
    df.groupby("district")["drought_class"].shift(-1)
)

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

df = df.dropna(
    subset=["target", "spi_3"]
).copy()

X = df[FEATURES]
y = df["target"]

print("\nTarget class distribution:")
print(y.value_counts())


# --------------------------------------------------
# 5. CHRONOLOGICAL TRAIN-TEST SPLIT
# --------------------------------------------------

split_date = df["date"].quantile(0.80)

train_mask = df["date"] < split_date
test_mask = df["date"] >= split_date

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]

y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

if X_train.empty or X_test.empty:
    raise ValueError("Training or testing dataset is empty.")

print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))
print("Split date:", split_date)


# --------------------------------------------------
# 6. BUILD RANDOM FOREST MODEL
# --------------------------------------------------

model = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
        ),
    ]
)


# --------------------------------------------------
# 7. TRAIN MODEL
# --------------------------------------------------

print("\nTraining Random Forest model...")

model.fit(X_train, y_train)

print("Training completed.")


# --------------------------------------------------
# 8. EVALUATE MODEL
# --------------------------------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions,
)

report = classification_report(
    y_test,
    predictions,
    output_dict=True,
    zero_division=0,
)

matrix = confusion_matrix(
    y_test,
    predictions,
    labels=model.classes_,
)

print("\n========== MODEL RESULTS ==========")

print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0,
    )
)

print("\nConfusion Matrix:")
print(matrix)

print("\nClasses:")
print(model.classes_)


# --------------------------------------------------
# 9. SAVE MODEL
# --------------------------------------------------

joblib.dump(model, MODEL_FILE)

print("\nModel saved at:")
print(MODEL_FILE)


# --------------------------------------------------
# 10. SAVE METRICS
# --------------------------------------------------

metrics = {
    "model": "Random Forest Classifier",
    "target": "Next-month SPI-derived drought category",
    "accuracy": float(accuracy),
    "split_date": str(split_date.date()),
    "training_records": int(len(X_train)),
    "testing_records": int(len(X_test)),
    "classes": list(model.classes_),
    "classification_report": report,
    "confusion_matrix": matrix.tolist(),
}

with open(METRICS_FILE, "w") as file:
    json.dump(metrics, file, indent=4)

print("\nMetrics saved at:")
print(METRICS_FILE)

print("\nDrought forecasting model training finished.")
