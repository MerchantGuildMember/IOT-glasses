"""Press Enter to take a photo, send it to the server, and hear the description.

Usage:
    python capture_and_describe.py                 # use a camera (Pi camera or USB webcam)
    python capture_and_describe.py --image cat.jpg # no camera yet: send a saved photo instead
"""

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from speak import speak

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000").rstrip("/")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "")
CAPTURE_DIR = HERE / "captures"


def take_photo() -> Path:
    """Try the Pi camera first, then a USB webcam."""
    CAPTURE_DIR.mkdir(exist_ok=True)
    path = CAPTURE_DIR / f"capture_{int(time.time())}.jpg"
    if shutil.which("rpicam-still"):
        result = subprocess.run(
            ["rpicam-still", "-n", "-t", "500", "--width", "1280", "--height", "960", "-o", str(path)],
            capture_output=True,
        )
        if result.returncode == 0 and path.exists():
            return path
    if shutil.which("fswebcam"):
        result = subprocess.run(["fswebcam", "-r", "1280x720", "--no-banner", str(path)], capture_output=True)
        if result.returncode == 0 and path.exists():
            return path
    raise RuntimeError("No camera found. Use --image <file> or install fswebcam for a USB webcam.")


def send_photo(path: Path) -> str:
    media_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    with path.open("rb") as f:
        response = requests.post(
            f"{SERVER_URL}/api/capture",
            headers={"X-Device-Token": DEVICE_TOKEN},
            files={"image": (path.name, f, media_type)},
            timeout=180,
        )
    response.raise_for_status()
    return response.json()["description"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, help="send this file instead of using a camera")
    args = parser.parse_args()

    if not DEVICE_TOKEN:
        raise SystemExit("DEVICE_TOKEN is not set. Copy pi/.env.example to pi/.env and fill it in.")

    speak("Smart glasses ready.")
    while True:
        try:
            input("\nPress Enter to describe what is in front of you (Ctrl+C to quit)...")
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        try:
            path = args.image if args.image else take_photo()
            print(f"Sending {path.name} to {SERVER_URL} ...")
            speak("Looking.")
            description = send_photo(path)
            if description:
                print("Description:", description)
                speak(description)
            else:
                print("Photo sent. No LLM connected, so there's no description yet.")
                speak("Photo sent.")
        except Exception as exc:
            print("Error:", exc)
            speak("Sorry, something went wrong.")


if __name__ == "__main__":
    main()
