import os
import json
import queue
import subprocess
import sounddevice as sd
from vosk import Model, KaldiRecognizer

MODEL_PATH = "/home/pi/my_dofbot_cli/models/vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
INPUT_DEVICE = 2


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

    print("Listening... say: home, hello, dance, pickup, or exit")
    print("Input device:", sd.query_devices(INPUT_DEVICE)["name"])

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=8000,
        dtype="int16",
        channels=1,
        device=INPUT_DEVICE,
        callback=callback
    ):
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip().lower()
                if text:
                    return text


def normalize_command(text: str) -> str | None:
    text = text.strip().lower()

    if "hello" in text:
        return "hello"
    if "home" in text or "go home" in text:
        return "home"
    if "dance" in text:
        return "dance"
    if "pick" in text or "pickup" in text:
        return "pickup"
    if text in {"exit", "quit", "stop"}:
        return "exit"

    return None


def run_cli_command(command: str):
    result = subprocess.run(
        ["python3", "/home/pi/my_dofbot_cli/cli_robot.py", command],
        capture_output=False,
        text=True
    )
    return result.returncode


def main():
    while True:
        spoken_text = listen_for_command()
        print(f"Recognized: {spoken_text}")

        command = normalize_command(spoken_text)
        if not command:
            print("Command not recognized. Try saying: home, hello, dance, pickup, or exit.\n")
            continue

        if command == "exit":
            print("Exiting voice control.")
            break

        run_cli_command(command)
        print()


if __name__ == "__main__":
    main()
