import sqlite3

DB_PATH = "robot.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT UNIQUE NOT NULL,
    hardware_action TEXT NOT NULL
)
""")

commands = [
    ("hello", "wave_hand"),
    ("home", "go_home"),
    ("pickup", "pick_object"),
    ("dance", "dance"),
]

for user_input, hardware_action in commands:
    cur.execute(
        "INSERT OR IGNORE INTO commands (user_input, hardware_action) VALUES (?, ?)",
        (user_input, hardware_action)
    )

conn.commit()
conn.close()

print("Database initialized: robot.db")