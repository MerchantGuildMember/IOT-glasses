"""Print temperature and humidity from the DHT22 every few seconds.

Wiring: see pi/WIRING.md. The DHT22 sometimes fails a read; that's normal, it just tries again.
"""

import time

import adafruit_dht
import board

sensor = adafruit_dht.DHT22(board.D4)  # GPIO4 = physical pin 7

print("Reading DHT22. Ctrl+C to stop.")
try:
    while True:
        try:
            print(f"Temperature: {sensor.temperature:.1f} C   Humidity: {sensor.humidity:.1f} %")
        except RuntimeError as err:
            print("Read failed, retrying:", err.args[0])
        time.sleep(3)
except KeyboardInterrupt:
    sensor.exit()
