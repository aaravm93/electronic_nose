import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# 1. Load dataset (Assumes samples.csv populated by collection script)
# Header format match: timestamp, mq3, mq135, temp, humidity, pressure, gas_res, label
data = pd.read_csv("data/samples.csv", header=None)

# Handle both 8-column and old-style row imports gracefully
if data.shape[1] >= 8:
    data = data.iloc[:, :8]
    data.columns = [
        "timestamp",
        "mq3",
        "mq135",
        "temp",
        "humidity",
        "pressure",
        "gas_res",
        "label"
        ]

    

# Filter strictly for target classes
target_classes = ["air", "alcohol", "vinegar", "coffee"]
data = data[data["label"].isin(target_classes)]

print("\nRaw samples per class:")
print(data["label"].value_counts())

# Core features: MQ-3, MQ-135, and single-temp BME680 Gas Resistance
features = ["mq3", "mq135", "gas_res"]

X_raw = data[features].astype(float)
y_raw = data["label"]

# --- STEP 1: CALCULATE BASELINE (R0) ---
# Baseline calculated from clean air samples
air_samples = X_raw[y_raw == "air"]
if len(air_samples) == 0:
    raise ValueError("Error: No 'air' samples found in dataset for baseline calibration!")

R0_train = air_samples.mean().values

# --- STEP 2: CONVERT ALL DATA TO RELATIVE RATIOS (R / R0) ---
X_ratios = X_raw / R0_train

# --- STEP 3: NOISE AUGMENTATION FOR AIR BASELINE ---
# Synthesize drift so model remains robust to ambient temperature/humidity changes
synthetic_air = []
for _ in range(1000):
    base_sample = air_samples.sample(1).values[0] / R0_train
    noise = np.random.uniform(0.98, 1.02, size=len(features))
    synthetic_air.append(base_sample * noise)

X_synthetic_df = pd.DataFrame(synthetic_air, columns=features)
y_synthetic = pd.Series(["air"] * 1000)

X_augmented = pd.concat([X_ratios, X_synthetic_df], ignore_index=True)
y_augmented = pd.concat([y_raw, y_synthetic], ignore_index=True)

# --- STEP 4: TRAIN MODEL ---
X_train, X_test, y_train, y_test = train_test_split(
    X_augmented, y_augmented, test_size=0.2, random_state=42, stratify=y_augmented
)

model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

# Evaluation
prediction = model.predict(X_test)
print(f"\nAccuracy: {accuracy_score(y_test, prediction) * 100:.2f}%")
print("\nClassification Report:\n", classification_report(y_test, prediction))
print("Confusion Matrix:\n", confusion_matrix(y_test, prediction))

# --- STEP 5: SAVE MODEL ARTIFACTS ---
joblib.dump({"model": model, "features": features, "R0": R0_train}, "model.joblib")

print("\nModel saved successfully as model.joblib!")
