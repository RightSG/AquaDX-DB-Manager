import json
import sqlite3
from tqdm import tqdm
from .diving_fish_prober import ProberAPIClient, get_music_data

with open("adm_config.json", "r") as f:
    config = json.load(f)

aqua_path = config["aqua_path"]
db_path = f"{aqua_path}/data/db.sqlite"

diving_fish_music_details_data = get_music_data()


def fetch_aqua_sqlite(user_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT music_id, level, achievement, combo_status, sync_status, deluxscore_max
        FROM maimai2_user_music_detail
        WHERE user_id = ?
        """,
        (user_id,),
    )
    records = cursor.fetchall()

    conn.close()
    return records


def parse_aqua_data(aqua_records):
    diving_fish_data = []

    # 创建一个包含所有 diving_fish_music_datails_data 中 id 的集合
    valid_song_ids = {int(song["id"]) for song in diving_fish_music_details_data}

    for record in aqua_records:
        if record[0] in valid_song_ids:
            music_detail = next(
                (
                    item
                    for item in diving_fish_music_details_data
                    if int(item["id"]) == record[0]
                ),
                None,
            )
            if music_detail:
                diving_fish_record = {
                    "song_id": record[0],
                    "level_index": record[1],
                    "achievements": parse_achievements(record[2]),
                    "fc": parse_combo_status(record[3]),
                    "fs": parse_sync_status(record[4]),
                    "dxScore": record[5],
                    "title": music_detail["title"],
                }
                diving_fish_data.append(diving_fish_record)

    return diving_fish_data


def parse_combo_status(fc_value):
    switcher = {1: "fc", 2: "fcp", 3: "ap", 4: "app"}
    return switcher.get(fc_value, "")


def parse_sync_status(fs_value):
    switcher = {5: "sync", 1: "fs", 2: "fsp", 3: "fsd", 4: "fsdp"}
    return switcher.get(fs_value, "")


def parse_achievements(achievements: int):
    parsed_achievements = achievements / 10000
    return round(parsed_achievements, 4)


def compare_combo_status(fc_value1, fc_value2):
    switcher = {"": 0, "fc": 1, "fcp": 2, "ap": 3, "app": 4}
    return switcher.get(fc_value1, 0) - switcher.get(fc_value2, 0)


def compare_sync_status(fs_value1, fs_value2):
    switcher = {"": 0, "fs": 1, "fsp": 2, "fsd": 3, "fsdp": 4, "sync": 5}
    return switcher.get(fs_value1, 0) - switcher.get(fs_value2, 0)


def aquadx_data_upload(user_id: int, overwrite: bool = False):
    """_summary_

    Args:
        user_id (int): 用于指示 db.sqlite 中的用户
        overwrite (bool, optional): 是否覆写（否则择优）. Defaults to False.
    """
    aqua_records = fetch_aqua_sqlite(user_id)
    aqua_to_diving_fish_records = parse_aqua_data(aqua_records)

    client = ProberAPIClient()

    diving_fish_player_records = client.get_player_full_scores(
        username=config["username"], password=config["password"]
    )

    combined_records = diving_fish_player_records["records"]

    if not overwrite:
        for record in tqdm(
            aqua_to_diving_fish_records, desc="Uploading data to diving-fish"
        ):
            song_id = record["song_id"]
            level_index = record["level_index"]
            for chart in combined_records:
                if chart["song_id"] == song_id and chart["level_index"] == level_index:
                    if record["achievements"] > chart["achievements"]:
                        chart["achievements"] = record["achievements"]

                    if compare_combo_status(record["fc"], chart["fc"]) > 0:
                        chart["fc"] = record["fc"]

                    if compare_sync_status(record["fs"], chart["fs"]) > 0:
                        chart["fs"] = record["fs"]
                    chart["title"] = record["title"]
                    break

            else:
                combined_records.append(record)
    else:
        combined_records = aqua_to_diving_fish_records

        client.delete_player_records(
            username=config["username"], password=config["password"]
        )

    records = []
    for record in combined_records:
        music_detail = next(
            (
                item
                for item in diving_fish_music_details_data
                if item["title"] == record["title"]
            ),
            None,
        )

        if music_detail:
            records.append(
                {
                    "achievements": record["achievements"],
                    "dxScore": record["dxScore"],
                    "fc": record["fc"],
                    "fs": record["fs"],
                    "level_index": record["level_index"],
                    "title": record["title"],
                    "type": music_detail["type"],
                }
            )

    response = client.update_records(
        username=config["username"],
        password=config["password"],
        records=records,
    )

    return response
