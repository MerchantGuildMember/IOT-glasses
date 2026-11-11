# Wiring guide (Raspberry Pi 4)

**Turn the Pi off before wiring.** Use the breadboard and jumper wires.
Pin numbers below are *physical* pin numbers: pin 1 is the corner pin nearest the SD card, marked with a square pad.
Pin 1 is on the inside row and pin 2 is on the edge row. Odd numbers continue down the inside row, even numbers down the edge.

```
        3V3  (1) (2)  5V
 SDA  GPIO2  (3) (4)  5V
 SCL  GPIO3  (5) (6)  GND
      GPIO4  (7) (8)
        GND  (9) (10)
     GPIO17 (11) (12) GPIO18
             ...
        3V3 (17) ...
```

All the sensors below run on **3.3 V**, so you don't need the logic level converter.

## 1. VL53L0X distance sensor (start with one)

| Sensor pin | Pi pin |
|---|---|
| VIN | 1 (3.3 V) |
| GND | 6 (GND) |
| SDA | 3 (GPIO2) |
| SCL | 5 (GPIO3) |

Leave the other pins (XSHUT, GPIO1) unconnected for now. You only need XSHUT later, when you add the second sensor.

Check that it's detected: `sudo raspi-config` → Interface Options → I2C → Enable, reboot, then run
`i2cdetect -y 1`. You should see **29** in the grid.

## 2. LED (proximity alert)

GPIO17 (pin 11) → **220–330 Ω resistor** → LED long leg. LED short leg → GND (pin 9).
The resistor stops the LED from burning out. If your PiHut LED kit didn't include resistors, any value from 220 Ω to 1 kΩ works.

## 3. DHT22 / AM2302 (temperature and humidity)

| Sensor | Pi pin |
|---|---|
| + / VCC (red wire on the AM2302) | 17 (3.3 V) |
| out / data (yellow) | 7 (GPIO4) |
| − / GND (black) | 9 or any GND |

If yours is the bare 4-pin DHT22 without a small board, also put a 10 kΩ resistor between data and 3.3 V. The AM2302 already has one built in.

## 4. Sound

**Easiest, for today:** plug earphones or any powered speaker into the Pi's 3.5 mm jack, then run
`sudo apt install espeak-ng` and `python speak.py`.

**Optional, later: MAX98357A amp with the small speaker**

| Amp pin | Pi pin |
|---|---|
| VIN | 2 (5 V) |
| GND | 14 (GND) |
| BCLK | 12 (GPIO18) |
| LRC | 35 (GPIO19) |
| DIN | 40 (GPIO21) |

Connect the speaker to the amp's + and − terminals. Then edit `/boot/firmware/config.txt`: change `dtparam=audio=on` to `#dtparam=audio=on`, add `dtoverlay=max98357a`, and reboot.

## 5. Camera

The OV2640/OV5640 boards with a flat cable are built for ESP32 or Arduino, so they **won't plug into the Pi's camera port**.
Options:
- a Raspberry Pi Camera Module (v2 or v3), which `rpicam-still` picks up
- any USB webcam (`sudo apt install fswebcam`)
- for the demo: `python capture_and_describe.py --image some_photo.jpg`

## Software setup on the Pi (once)

```bash
cd ~/IOT-glasses/pi
python3 -m venv --system-site-packages .venv   # system packages give you gpiozero
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # then edit SERVER_URL and DEVICE_TOKEN
```

Fritzing: the brief wants a Fritzing sketch of this wiring. Fritzing has parts for the Pi 4, DHT22, LED and resistor. Search "VL53L0X" in its parts bin, or use the Adafruit Fritzing library.
