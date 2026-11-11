"""Say text out loud through the Pi's audio output (3.5mm jack or the I2S amp).

Needs espeak-ng:  sudo apt install espeak-ng
"""

import shutil
import subprocess
import sys


def speak(text: str) -> None:
    if not text:
        return
    if shutil.which("espeak-ng") is None:
        print("[speak] espeak-ng not installed, printing instead:", text)
        return
    # -s 150 = words per minute, a calm speaking speed
    subprocess.run(["espeak-ng", "-s", "150", text], check=False)


if __name__ == "__main__":
    speak(" ".join(sys.argv[1:]) or "Hello, the smart glasses are working.")
