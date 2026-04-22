import sys
import psycopg2

from hardware import wave_hand, go_home, pick_object, dance


def get_db_connection():
    return psycopg2.connect(
        dbname="robot",
        user="robot_user",
        password="arrianaf",   # change if you set a different password
        host="localhost",
        port="5432"
    )


def get_hardware_action(user_input: str):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT hardware_action FROM commands WHERE user_input = %s",
        (user_input,)
    )
    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row[0]
    return None


def execute_action(action: str):
    actions = {
        "wave_hand": wave_hand,
        "go_home": go_home,
        "pick_object": pick_object,
        "dance": dance,
    }

    func = actions.get(action)
    if not func:
        print(f"Unknown hardware action: {action}")
        return

    func()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 cli_robot.py <command>")
        print("Example: python3 cli_robot.py hello")
        return

    user_input = sys.argv[1].strip().lower()
    action = get_hardware_action(user_input)

    if not action:
        print(f"No database mapping found for command: {user_input}")
        return

    print(f"Matched command '{user_input}' -> '{action}'")
    execute_action(action)


if __name__ == "__main__":
    main()