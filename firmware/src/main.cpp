#include <Arduino.h>
#include <Wire.h>

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_BME680.h>

#define SDA_PIN 8
#define SCL_PIN 9

#define OLED_MOSI 11
#define OLED_CLK  12
#define OLED_DC   13
#define OLED_CS   15
#define OLED_RESET 10

#define COFFEE_HEATER_TEMP 320 
#define COFFEE_HEATER_TIME 150 

Adafruit_SSD1306 display(
  128,
  64,
  OLED_MOSI,
  OLED_CLK,
  OLED_DC,
  OLED_RESET,
  OLED_CS
);

Adafruit_ADS1115 ads;
Adafruit_BME680 bme;

unsigned long lastReadingTime = 0;
const unsigned long sampleInterval = 170;

void oled(String text) {
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 20);
  display.println(text);
  display.display();
}

void setup() {
  Serial.begin(115200);

  Wire.begin(SDA_PIN, SCL_PIN);

  display.begin(SSD1306_SWITCHCAPVCC);


  ads.begin();
  ads.setDataRate(RATE_ADS1115_860SPS);
  ads.setGain(GAIN_TWOTHIRDS);

  if (!bme.begin()) {
    Serial.println("BME680 connection failed!");
  }

  bme.setTemperatureOversampling(BME680_OS_2X);
  bme.setHumidityOversampling(BME680_OS_1X);
  bme.setPressureOversampling(BME680_OS_1X);

  bme.setGasHeater(COFFEE_HEATER_TEMP, COFFEE_HEATER_TIME);

  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("OLED")) {
      oled(cmd.substring(5));
    }
  }

  unsigned long currentMillis = millis();
  if (currentMillis - lastReadingTime >= sampleInterval) {
    lastReadingTime = currentMillis;

    int mq3   = ads.readADC_SingleEnded(0);
    int mq135 = ads.readADC_SingleEnded(1);

    if (bme.performReading()) {
      Serial.print("DATA,");
      Serial.print(currentMillis);
      Serial.print(",");
      Serial.print(mq3);
      Serial.print(",");
      Serial.print(mq135);
      Serial.print(",");
      Serial.print(bme.temperature);
      Serial.print(",");
      Serial.print(bme.humidity);
      Serial.print(",");
      Serial.print(bme.pressure / 100.0);
      Serial.print(",");
      Serial.print(bme.gas_resistance);
      Serial.println();
    }
  }
}