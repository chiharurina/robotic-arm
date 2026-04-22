import sys
import time
import sqlite3

# Yahboom arm library copied from Docker
sys.path.append("/home/pi/my_dofbot_cli/vendor/Arm_Lib")
from Arm_Lib import Arm_Device

arm = Arm_Device()

DB_PATH = "/home/pi/my_dofbot_cli/robot.db"


def execute_action(action: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT hardware_action FROM commands WHERE user_input = ?",
        (action.strip().lower(),)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        print(f"No database mapping found for command: {action}")
        return

    hardware_action = row[0]
    print(f"Matched command '{action}' -> '{hardware_action}'")

    if hardware_action == "go_home":
        print("Running real hardware action: go_home")
        arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 180, 1000)
        time.sleep(2)

    elif hardware_action == "wave_hand":
        print("Running real hardware action: wave_hand")
        arm.Arm_serial_servo_write(2, 60, 800)
        time.sleep(1)
        for _ in range(3):
            arm.Arm_serial_servo_write(4, 70, 400)
            time.sleep(0.5)
            arm.Arm_serial_servo_write(4, 110, 400)
            time.sleep(0.5)
        arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 180, 1000)
        time.sleep(2)

    elif hardware_action == "dance":
        print("Running real hardware action: dance")
        arm.Arm_serial_servo_write(1, 75, 600)
        time.sleep(0.6)
        arm.Arm_serial_servo_write(1, 105, 600)
        time.sleep(0.6)
        arm.Arm_serial_servo_write(1, 75, 600)
        time.sleep(0.6)
        arm.Arm_serial_servo_write(1, 105, 600)
        time.sleep(0.6)
        arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 180, 1000)
        time.sleep(2)

    else:
        print(f"Mapped action found, but not implemented yet: {hardware_action}")


if __name__ == "__main__":
    while True:
        cmd = input("Enter command (home / hello / dance / exit): ").strip().lower()
        if cmd in {"exit", "quit"}:
            print("Exiting.")
            break
        execute_action(cmd)