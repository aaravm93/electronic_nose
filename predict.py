import sys
import select
import serial
import joblib
import pandas as pd
import numpy as np

# Load model pipeline
saved_data = joblib.load("model.joblib")
model = saved_data["model"]
feature_names = saved_data["features"]

PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
CALIBRATION_SAMPLES = 10

# HIGH SENSITIVITY SETTINGS
# ALPHA = 0.6 means 60% weight on raw reading (faster response to subtle scents)
ALPHA = 0.6 
# CONFIDENCE_THRESHOLD = 0.45 catches subtle class signals instead of declaring 'purging'
CONFIDENCE_THRESHOLD = 0.6

smoothed_ratios = None

def calibrate_baseline(ser_conn, num_samples=CALIBRATION_SAMPLES):
    """Calculates live R0 values in clean air."""
    print("\n" + "=" * 55)
    print("CALIBRATING: Place sensor in CLEAN AIR.")
    print(f"Collecting {num_samples} baseline samples...")
    print("=" * 55)

    ser_conn.reset_input_buffer()
    collected = []

    while len(collected) < num_samples:
        line = ser_conn.readline().decode("utf-8", errors="ignore").strip()
        if line.startswith("DATA"):
            parts = line.split(",")
            try:
                raw_features = [
                    float(parts[2]),  # MQ-3
                    float(parts[3]),  # MQ-135
                    float(parts[7])   # BME Gas Resistance
                ]
                collected.append(raw_features)
                print(f"  Calibration sample {len(collected)}/{num_samples}")
            except (IndexError, ValueError):
                continue

    R0_live = np.mean(collected, axis=0)
    print("\nCalibration Complete! Live R0 Baseline:")
    for name, val in zip(feature_names, R0_live):
        print(f"  {name:8s}: {val:.1f}")
    print("-" * 55)
    print(">>> Press 'r' + ENTER to recalibrate <<<\n")
    return R0_live

ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
R0 = calibrate_baseline(ser)

print("Starting high-sensitivity classification...")

try:
    while True:
        if select.select([sys.stdin], [], [], 0.001)[0]:
            if sys.stdin.readline().strip().lower() == "r":
                R0 = calibrate_baseline(ser)
                smoothed_ratios = None
                continue

        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if line.startswith("DATA"):
            parts = line.split(",")
            try:
                raw_features = [float(parts[2]), float(parts[3]), float(parts[7])]
                live_ratios = np.array(raw_features) / R0

                if smoothed_ratios is None:
                    smoothed_ratios = live_ratios
                else:
                    smoothed_ratios = (ALPHA * live_ratios) + ((1 - ALPHA) * smoothed_ratios)

                features_df = pd.DataFrame([smoothed_ratios], columns=feature_names)
                probabilities = model.predict_proba(features_df)[0]
                confidence = np.max(probabilities)
                predicted_label = model.classes_[np.argmax(probabilities)]

                # Reduced threshold for subtle scents
                if confidence < CONFIDENCE_THRESHOLD:
                    predicted_label = "purging"

                ser.write(f"OLED {predicted_label}\n".encode("utf-8"))

                r_str = ", ".join([f"{r:.2f}" for r in smoothed_ratios])
                print(f"Pred: {predicted_label:<10} | Conf: {confidence*100:3.0f}% | Ratios: [{r_str}]")

            except (IndexError, ValueError):
                continue

except KeyboardInterrupt:
    print("\nExiting prediction loop.")
    ser.close()