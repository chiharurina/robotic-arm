import sys
import time

sys.path.append("/home/pi/my_dofbot_cli/vendor/Arm_Lib")
from Arm_Lib import Arm_Device

arm = Arm_Device()


def move_joint(joint: int, angle: int | float, speed: int):
    arm.Arm_serial_servo_write(int(joint), int(angle), int(speed))
    time.sleep(speed / 1000.0)


def move_joints(joints: list, speed: int):
    arm.Arm_serial_servo_write6(
        int(joints[0]),
        int(joints[1]),
        int(joints[2]),
        int(joints[3]),
        int(joints[4]),
        int(joints[5]),
        int(speed),
    )
    time.sleep(speed / 1000.0)


def hand_open(speed: int = 400):
    arm.Arm_serial_servo_write(6, 135, int(speed))
    time.sleep(speed / 1000.0)


def hand_close(speed: int = 400):
    arm.Arm_serial_servo_write(6, 180, int(speed))
    time.sleep(speed / 1000.0)


def sleep_seconds(seconds: float):
    time.sleep(float(seconds))