import sys
import json
import re
import subprocess
from datetime import datetime

import psycopg2

from hardware import move_joint, move_joints, hand_open, hand_close, sleep_seconds


DB_CONFIG = {
    "dbname": "robot",
    "user": "robot_user",
    "password": "arrianaf",
    "host": "localhost",
    "port": "5432",
}

JOINT_LIMITS = {
    1: (0, 180),
    2: (60, 120),
    3: (60, 120),
    4: (60, 120),
    5: (0, 180),
    6: (135, 180),
}

MIN_SPEED = 100
MAX_SPEED = 2500
MAX_SLEEP = 5.0

ROS_ACTION_SERVICES = {
    "go_home": "/go_home",
    "wave_hand": "/wave_hand",
    "dance": "/dance",
    "pick_up_object": "/pick_up_object",
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def normalize_command(user_text: str) -> str:
    text = user_text.strip().lower()

    home_phrases = [
        "home", "go home", "go to home", "go to home position",
        "return home", "return to home", "reset", "reset position",
        "go back home",
    ]

    rest_phrases = [
        "rest", "rest position", "go to rest", "return to rest",
        "idle", "idle position", "park", "park arm",
    ]

    hello_phrases = [
        "hello", "wave", "wave hand", "say hello", "do hello", "greet",
    ]

    dance_phrases = [
        "dance", "do a dance", "start dancing", "dance now",
    ]

    pickup_phrases = [
        "pickup", "pick up", "pick", "pick up object", "pick up the object",
        "grab object", "grab the object", "grab tool", "grab the tool",
        "pick up the tool",
    ]

    open_hand_phrases = [
        "open hand", "open the hand", "open gripper", "open the gripper",
        "release", "release object",
    ]

    close_hand_phrases = [
        "close hand", "close the hand", "close gripper", "close the gripper",
        "grip", "grab",
    ]

    point_left_phrases = [
        "point left", "look left", "turn left", "move left", "aim left",
    ]

    point_right_phrases = [
        "point right", "look right", "turn right", "move right", "aim right",
    ]

    if text in home_phrases:
        return "go_home"
    if text in rest_phrases:
        return "rest_position"
    if text in hello_phrases:
        return "wave_hand"
    if text in dance_phrases:
        return "dance"
    if text in pickup_phrases:
        return "pick_up_object"
    if text in open_hand_phrases:
        return "open_hand"
    if text in close_hand_phrases:
        return "close_hand"
    if text in point_left_phrases:
        return "point_left"
    if text in point_right_phrases:
        return "point_right"

    return text


def split_commands(user_text: str) -> list[str]:
    text = user_text.strip().lower()
    text = text.replace(" and then ", " then ")
    text = text.replace(" then ", "|")
    text = text.replace(" and ", "|")
    text = text.replace(",", "|")
    parts = [p.strip() for p in text.split("|") if p.strip()]
    return [normalize_command(p) for p in parts]


def get_action_steps(action_name: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.name, av.version_no, av.steps
        FROM actions a
        JOIN action_versions av ON a.id = av.action_id
        WHERE a.name = %s AND av.is_active = TRUE
        ORDER BY av.version_no DESC
        LIMIT 1
        """,
        (action_name,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "action_name": row[0],
        "version_no": row[1],
        "steps": row[2],
    }


def validate_speed(speed: int):
    if not isinstance(speed, (int, float)):
        raise ValueError(f"Invalid speed type: {speed}")
    if not (MIN_SPEED <= int(speed) <= MAX_SPEED):
        raise ValueError(f"Unsafe speed: {speed} (allowed {MIN_SPEED}-{MAX_SPEED})")


def validate_angle(joint: int, angle: int | float):
    if joint not in JOINT_LIMITS:
        raise ValueError(f"Invalid joint: {joint}")
    low, high = JOINT_LIMITS[joint]
    if not isinstance(angle, (int, float)):
        raise ValueError(f"Invalid angle type for joint {joint}: {angle}")
    if not (low <= float(angle) <= high):
        raise ValueError(f"Unsafe angle for joint {joint}: {angle} (allowed {low}-{high})")


def validate_sleep(seconds: float):
    if not isinstance(seconds, (int, float)):
        raise ValueError(f"Invalid sleep type: {seconds}")
    if not (0 <= float(seconds) <= MAX_SLEEP):
        raise ValueError(f"Unsafe sleep duration: {seconds} (allowed 0-{MAX_SLEEP})")


def validate_steps(steps):
    try:
        if not isinstance(steps, list):
            return False, "Steps must be a list"

        for i, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                return False, f"Step {i}: must be an object"
            if "type" not in step:
                return False, f"Step {i}: missing 'type'"

            step_type = step["type"]

            if step_type == "move_joints":
                if "joints" not in step or "speed" not in step:
                    return False, f"Step {i}: move_joints requires 'joints' and 'speed'"
                joints = step["joints"]
                if not isinstance(joints, list) or len(joints) != 6:
                    return False, f"Step {i}: move_joints must have exactly 6 joint values"
                validate_speed(step["speed"])
                for joint_id, angle in enumerate(joints, start=1):
                    validate_angle(joint_id, angle)

            elif step_type == "move_joint":
                if "joint" not in step or "angle" not in step or "speed" not in step:
                    return False, f"Step {i}: move_joint requires 'joint', 'angle', and 'speed'"
                validate_speed(step["speed"])
                validate_angle(int(step["joint"]), step["angle"])

            elif step_type == "hand":
                if "state" not in step:
                    return False, f"Step {i}: hand requires 'state'"
                if step["state"] not in ["open", "close"]:
                    return False, f"Step {i}: hand state must be 'open' or 'close'"
                if "speed" in step:
                    validate_speed(step["speed"])

            elif step_type == "sleep":
                if "seconds" not in step:
                    return False, f"Step {i}: sleep requires 'seconds'"
                validate_sleep(step["seconds"])

            else:
                return False, f"Step {i}: unknown step type '{step_type}'"

        return True, "Validation passed"

    except Exception as exc:
        return False, str(exc)


def execute_steps_locally(steps):
    for i, step in enumerate(steps, start=1):
        step_type = step["type"]

        if step_type == "move_joints":
            print(f"Step {i}: move_joints -> {step['joints']} speed={step['speed']}")
            move_joints(step["joints"], step["speed"])

        elif step_type == "move_joint":
            print(
                f"Step {i}: move_joint -> joint={step['joint']} angle={step['angle']} speed={step['speed']}"
            )
            move_joint(step["joint"], step["angle"], step["speed"])

        elif step_type == "hand":
            print(f"Step {i}: hand -> {step['state']}")
            speed = step.get("speed", 400)
            if step["state"] == "open":
                hand_open(speed)
            else:
                hand_close(speed)

        elif step_type == "sleep":
            print(f"Step {i}: sleep -> {step['seconds']}s")
            sleep_seconds(step["seconds"])


def call_ros_service(service_name: str) -> tuple[bool, str]:
    cmd = [
        "docker", "exec", "-i", "ros2_dofbot",
        "bash", "-lc",
        (
            "source /opt/ros/jazzy/setup.bash && "
            "source /root/ros2_dofbot_ws/install/setup.bash && "
            f"ros2 service call {service_name} std_srvs/srv/Trigger"
        ),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as exc:
        return False, f"ROS call failed to start: {exc}"

    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")

    if result.returncode != 0:
        return False, output.strip()

    if "success=True" in output or "success: true" in output.lower():
        return True, output.strip()

    return False, output.strip()


def execute_action(action_name: str, steps):
    if action_name in ROS_ACTION_SERVICES:
        service_name = ROS_ACTION_SERVICES[action_name]
        print(f"Executing via ROS service: {service_name}")
        return call_ros_service(service_name)

    print(f"Executing locally: {action_name}")
    execute_steps_locally(steps)
    return True, "Executed locally"


def log_execution(requested_text, action_name, status, error_message, telemetry, started_at, finished_at):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO execution_logs (
            requested_text, action_name, status, error_message, telemetry, started_at, finished_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            requested_text,
            action_name,
            status,
            error_message,
            json.dumps(telemetry),
            started_at,
            finished_at,
        )
    )
    conn.commit()
    cur.close()
    conn.close()


def run_single_action(requested_text: str, action_name: str):
    started_at = datetime.now()

    action_data = get_action_steps(action_name)
    if not action_data:
        print(f"No database action found for: {action_name}")
        log_execution(
            requested_text=requested_text,
            action_name=action_name,
            status="failed",
            error_message="Action not found in database",
            telemetry={"message": "database lookup failed"},
            started_at=started_at,
            finished_at=datetime.now(),
        )
        return False

    steps = action_data["steps"]
    is_valid, message = validate_steps(steps)

    if not is_valid:
        print(f"Validation failed for {action_name}: {message}")
        log_execution(
            requested_text=requested_text,
            action_name=action_name,
            status="failed",
            error_message=message,
            telemetry={"message": "validation failed"},
            started_at=started_at,
            finished_at=datetime.now(),
        )
        return False

    try:
        print(f"\nExecuting action: {action_data['action_name']}")
        print(f"Version: {action_data['version_no']}")
        success, execution_message = execute_action(action_name, steps)

        if not success:
            print(f"Execution failed for {action_name}: {execution_message}")
            log_execution(
                requested_text=requested_text,
                action_name=action_name,
                status="failed",
                error_message=execution_message,
                telemetry={"message": "execution failed"},
                started_at=started_at,
                finished_at=datetime.now(),
            )
            return False

        print("Execution complete.")
        log_execution(
            requested_text=requested_text,
            action_name=action_name,
            status="success",
            error_message=None,
            telemetry={"message": execution_message},
            started_at=started_at,
            finished_at=datetime.now(),
        )
        return True

    except Exception as exc:
        print(f"Execution failed for {action_name}: {exc}")
        log_execution(
            requested_text=requested_text,
            action_name=action_name,
            status="failed",
            error_message=str(exc),
            telemetry={"message": "execution exception"},
            started_at=started_at,
            finished_at=datetime.now(),
        )
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cli_robot.py <command>")
        print("Examples:")
        print("  python3 cli_robot.py home")
        print("  python3 cli_robot.py 'home then dance'")
        return

    requested_text = sys.argv[1].strip().lower()
    commands = split_commands(requested_text)
    print("Parsed commands:", commands)

    if not commands:
        print("No commands found.")
        return

    for cmd in commands:
        if cmd in {"stop", "emergency_stop"}:
            print("Emergency stop requested. Remaining commands skipped.")
            break

        success = run_single_action(requested_text, cmd)
        if not success:
            print(f"Stopping sequence because '{cmd}' failed.")
            break


if __name__ == "__main__":
    main()
