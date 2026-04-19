import sys
import time

# Add Yahboom library path
sys.path.append("/home/pi/my_dofbot_cli/vendor/Arm_Lib")
from Arm_Lib import Arm_Device

# Initialize arm
arm = Arm_Device()


def go_home():
    print("Executing hardware action: go_home")
    arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 180, 1000)
    time.sleep(2)


def wave_hand():
    print("Executing hardware action: wave_hand")
    go_home()

    # lift arm slightly
    arm.Arm_serial_servo_write(2, 60, 800)
    time.sleep(1)

    # wave motion (wrist joint)
    for _ in range(3):
        arm.Arm_serial_servo_write(4, 70, 400)
        time.sleep(0.5)
        arm.Arm_serial_servo_write(4, 110, 400)
        time.sleep(0.5)

    go_home()


def dance():
    print("Executing hardware action: dance")
    go_home()

    # move base left/right
    for _ in range(2):
        arm.Arm_serial_servo_write(1, 75, 600)
        time.sleep(0.6)
        arm.Arm_serial_servo_write(1, 105, 600)
        time.sleep(0.6)

    # up/down + wrist combo
    for _ in range(2):
        arm.Arm_serial_servo_write(2, 70, 400)
        arm.Arm_serial_servo_write(4, 70, 400)
        time.sleep(0.5)
        arm.Arm_serial_servo_write(2, 110, 400)
        arm.Arm_serial_servo_write(4, 110, 400)
        time.sleep(0.5)

    # gripper open/close
    for _ in range(2):
        arm.Arm_serial_servo_write(6, 150, 300)
        time.sleep(0.4)
        arm.Arm_serial_servo_write(6, 180, 300)
        time.sleep(0.4)

    go_home()


def pick_object():
    print("Executing hardware action: pick_object")
    print("TODO: implement pick sequence")