"""Read the VL53L0X distance sensor and light an LED when something is close.

Wiring: see pi/WIRING.md. Needs I2C turned on (sudo raspi-config > Interface Options > I2C).
"""

import time

import adafruit_vl53l0x
import board
import busio
from gpiozero import LED

ALERT_MM = 500      # light the LED when something is closer than 50 cm
LED_PIN = 17        # GPIO17 = physical pin 11

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_vl53l0x.VL53L0X(i2c)
led = LED(LED_PIN)

print("Reading distance. Ctrl+C to stop.")
try:
    while True:
        distance_mm = sensor.range
        too_close = 0 < distance_mm < ALERT_MM
        led.value = too_close
        bar = "#" * min(40, distance_mm // 50)
        print(f"{distance_mm:5d} mm  {bar}{'   <-- TOO CLOSE' if too_close else ''}")
        time.sleep(0.1)
except KeyboardInterrupt:
    led.off()
