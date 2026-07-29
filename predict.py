import serial
import joblib
import numpy as np

# 1. Load the saved dictionary
saved_data = joblib.load("model.joblib")

# 2. Extract the actual model from the dictionary
# Note: If your training script saved the model under a different key 
# (like 'classifier' or 'clf'), change the key below.
# If you get a KeyError, uncomment the next line to see the available keys:
# print("Keys in saved file:", saved_data.keys())
model = saved_data["model"]

PORT = "/dev/ttyACM0"
BAUD_RATE = 115200

# Open serial communication
ser = serial.Serial(PORT, BAUD_RATE, timeout=1)

print(f"Listening for sensor data on {PORT}...")

try:
    while True:
        # Read incoming line from ESP32
        line = ser.readline().decode('utf-8', errors='ignore').strip()

        # Check for DATA prefix matching your CSV collection format
        if line.startswith("DATA"):
            parts = line.split(",")

            try:
                raw_values = parts[1:]  # Drops 'DATA'


                features = [
                    float(raw_values[1]),  # mq3
                    float(raw_values[2]),  # mq135
                    float(raw_values[6]),  # gas res
                ]

                # Convert to 2D numpy array for scikit-learn
                features_array = np.array([features])

                # Predict label
                prediction = model.predict(features_array)[0]

                # Format payload for ESP32
                output_msg = f"OLED {prediction}\n"
                
                # Write response back to ESP32 over Serial
                ser.write(output_msg.encode('utf-8'))
                
                print(f"Sensors: {features} --> Sent: OLED {prediction}")

            except (IndexError, ValueError) as e:
                print(f"Malformed data line: {line} | Error: {e}")

except KeyboardInterrupt:
    print("\nStopping prediction script.")
    ser.close()