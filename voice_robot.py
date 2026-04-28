import os
import json
import queue
import subprocess
import sounddevice as sd
from vosk import Model, KaldiRecognizer

MODEL_PATH = "/home/pi/my_dofbot_cli/models/vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
INPUT_DEVICE_NAME = "Blue Snowball"


def listen_for_command() -> str:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Vosk model folder not found: {MODEL_PATH}")

    q = queue.Queue()
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    def callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(bytes(indata))

    devices = sd.query_devices()
    input_device_index = None

    for i, dev in enumerate(devices):
        if INPUT_DEVICE_NAME.lower() in dev["name"].lower() and dev["max_input_channels"] > 0:
            input_device_index = i
            break

    if input_device_index is None:
        raise RuntimeError(f"Could not find input device matching: {INPUT_DEVICE_NAME}")

    print("Listening... say commands like: home then dance, pickup and home, or exit")
    print("Input device:", sd.query_devices(input_device_index)["name"])

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        device=input_device_index,
        callback=callback
        ):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip().lower()
                if text:
                    return text


def run_cli_command(command_text: str):
    return subprocess.run(
        ["python3", "/home/pi/my_dofbot_cli/cli_robot.py", command_text],
        capture_output=False,
        text=True
    ).returncode


def main():
    while True:
        spoken_text = listen_for_command()
        print(f"Recognized: {spoken_text}")

        if spoken_text in {"exit", "quit", "stop"}:
            print("Exiting voice control.")
            break

        run_cli_command(spoken_text)
        print()


if __name__ == "__main__":
    main()