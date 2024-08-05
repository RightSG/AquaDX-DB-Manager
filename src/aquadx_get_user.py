import json
import sqlite3

with open("adm_config.json", "r") as f:
    config = json.load(f)

default_aqua_path = config["aqua_path"]
default_db_path = f"{default_aqua_path}/data/db.sqlite"


def get_user(db_path=default_db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_name, player_rating FROM maimai2_user_detail")
    rows = cursor.fetchall()

    users = [
        {"id": row[0], "user_name": row[1], "player_rating": row[2]} for row in rows
    ]

    cursor.close()
    conn.close()

    return users
