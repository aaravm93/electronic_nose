# Introduction
An ESP32-S3-based electronic nose prototype that samples gas sensors, trains a
Random Forest classifier from labeled readings, and classifies live readings.
The Python pipeline currently only uses the MQ-3, MQ-135, and BME680 gas-resistance
reading at a single temperature to predict the substance. I have used different temperature sensor readings of BME688 before, but finally chose to use only one temperature because of the speed we get when collecting data. The ESP32 also reads the BME680 temperature, humidity, and pressure values and sends all readings over USB serial. The temperature, pressure and humidity aren't used now, but can be used in the future to study its effect on the sensor values.

## Hardware and firmware

The firmware is in [`firmware/`](firmware/) and is configured for the
`esp32-s3-devkitc-1` board with the Arduino framework. The hardware in
[`firmware/src/main.cpp`](firmware/src/main.cpp) includes:

- ESP32-S3 development board
- ADS1115 ADC, with MQ-3 on input 0 and MQ-135 on input 1
- BME680 environmental sensor
- SSD1306 128x64 OLED display

### Pin connections

These are the pin assignments configured in
[`firmware/src/main.cpp`](firmware/src/main.cpp):

ADS1115 and BME680 share the I2C bus:
SDA - ESP32-S3 GPIO 8
SCL - ESP32-S3 GPIO 9

MQ-3 analog output (AO)   - ADS1115 A0 (channel 0)
MQ-135 analog output (AO) - ADS1115 A1 (channel 1)

OLED (software SPI):
MOSI / DIN - ESP32-S3 GPIO 11
CLK / SCK - ESP32-S3 GPIO 12
DC - ESP32-S3 GPIO 13
RESET / RES - ESP32-S3 GPIO 10
CS - ESP32-S3 GPIO 15

The OLED is configured for software SPI, while the ADS1115 and BME680 share
the I2C bus. The firmware does not specify power or ground pins: connect those
according to the breakout-board requirements, and use a common ground. Check
that the MQ module analog-output voltage is safe for the ADS1115 and its
configured supply before connecting it.

Install [PlatformIO Core](https://platformio.org/install/cli), connect the
board, and upload the firmware.

The firmware communicates at **115200 baud**. It sends readings as
comma-separated lines in this order:

```text
DATA,timestamp_ms,mq3_adc,mq135_adc,temperature_c,humidity_pct,pressure_hpa,gas_resistance_ohms
```

The Python scripts currently use `/dev/ttyACM0` as the serial device. You must chnage this port according to the port your system assigns by updatiing `PORT` in `collect.py` and `predict.py`
before running them. Only one script can use the serial connection at a time.

## Python setup

Python dependencies used by the scripts are `pyserial`, `pandas`, `numpy`,
`scikit-learn`, and `joblib`. Create an environment and install them with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pyserial pandas numpy scikit-learn joblib
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Collect labeled samples

With the firmware running, collect one class at a time. Pass the label as the
first argument; the script appends readings to `data/samples.csv`:

```bash
python collect.py air
python collect.py alcohol
python collect.py vinegar
python collect.py coffee
```

Stop collection with **Ctrl+C**. Collect representative samples for each class
under consistent conditions. The collector appends rows without a header, in
this format:

```text
timestamp_ms,mq3_adc,mq135_adc,temperature_c,humidity_pct,pressure_hpa,gas_resistance_ohms,label
```

`train.py` currently trains only on the labels `air`, `alcohol`, `vinegar`,
and `coffee`. This can be changed according to your needs. It requires at least some `air` samples to calculate the baseline. The path to the CSV must be specified in `train.py`

## Train the classifier

After collecting data for all target classes, run:

```bash
python train.py
```

Training reports the test-set accuracy, classification report, and confusion
matrix, then writes `model.joblib` in the repository root. The model uses
three features: MQ-3, MQ-135 and BME680 gas resistance. They are normalized by their mean
values from the `air` samples. The baseline-ratio approach was found through
lots of trial and error. You may try other configurations and experiment to find out what works best by editing `train.py`:

Change `features` to select which sensor columns are used. Keep these names consistent with the dataset columns and the feature names expected by `predict.py`.
Change `target_classes` to choose which labels are included in training. Keep `air` included because it is used to calculate the baseline.
Adjust the synthetic `air` augmentation: the loop currently generates `1000` samples, with each feature perturbed by a random factor from `0.98` to `1.02`.
Tune `test_size` and `random_state` in `train_test_split` to change the evaluation split, and `n_estimators` and `class_weight` in `RandomForestClassifier` to experiment with the classifier.

After changing a setting, retrain and compare the classification report and
confusion matrix. You can also find better approaches to train. The dataset path is set in the `pd.read_csv(...)` line.

## Run live prediction

With the model trained and the board connected, start:

```bash
python predict.py
```

At startup, we must keep the sensor in clean air while it collects 10 baseline readings. One thing that i have noticed is alcohol vapours remain in the air for several seconds. So if alcohol was the last sample used, I would recommend waiting some time before collecting the baseline. It then smooths the live feature ratios and prints the predicted class and confidence. Predictions below the configured confidence threshold are displayed as `purging`. The predicted substance name is sent to the firmware for display on the OLED. Enter `r` and press **Enter** to recalibrate the clean-air baseline; use **Ctrl+C** to exit.

## Repository layout

```text
collect.py             Capture labeled samples from the serial stream
train.py               Train and evaluate the Random Forest classifier
predict.py             Calibrate and classify live sensor readings
model.joblib           Model artifact used by predict.py (generated by train.py)
data/samples.csv       Labeled training data used by train.py
firmware/              PlatformIO ESP32-S3 firmware project
```

The additional `model1.joblib` through `model4.joblib` files and the other CSV
files are not used by the current training/prediction commands.
<img width="4032" height="3024" alt="IMG_5991" src="https://github.com/user-attachments/assets/651a46fe-78d0-4e0a-8f15-797085a4fbc4" />
<img width="4032" height="3024" alt="IMG_5993" src="https://github.com/user-attachments/assets/a9586360-9679-4769-8af5-2e2ca8d61974" />
<img width="5712" height="4284" alt="IMG_5992" src="https://github.com/user-attachments/assets/02ebc153-c032-41f7-9c2c-e32d2ed92f9a" />
<img width="1056" height="1133" alt="image" src="https://github.com/user-attachments/assets/96d95ee6-cf14-442e-83b1-0f68607bc921" />
