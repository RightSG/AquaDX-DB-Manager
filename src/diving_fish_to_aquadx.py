import json
import sqlite3
from tqdm import tqdm

with open("adm_config.json", "r") as f:
    config = json.load(f)

aqua_path = config["aqua_path"]
db_path = f"{aqua_path}/data/db.sqlite"


class song_score:
    def __init__(
        self,
        id,
        music_id,
        level,
        play_count,
        achievement,
        combo_status,
        sync_status,
        deluxscore_max,
        score_rank,
        user_id,
        ext_num1,
    ):
        self.id = id
        self.music_id = music_id
        self.level = level
        self.play_count = play_count
        self.achievement = achievement
        self.combo_status = combo_status
        self.sync_status = sync_status
        self.deluxscore_max = deluxscore_max
        self.score_rank = score_rank
        self.user_id = user_id
        self.ext_num1 = ext_num1

    def insert_into_db(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO maimai2_user_music_detail (
                id, music_id, level, play_count, achievement, combo_status, 
                sync_status, deluxscore_max, score_rank, user_id, ext_num1
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.id,
                self.music_id,
                self.level,
                self.play_count,
                self.achievement,
                self.combo_status,
                self.sync_status,
                self.deluxscore_max,
                self.score_rank,
                self.user_id,
                self.ext_num1,
            ),
        )
        conn.commit()

    def update_in_db(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE maimai2_user_music_detail
            SET play_count = ?, achievement = ?, combo_status = ?, 
                sync_status = ?, deluxscore_max = ?, score_rank = ?, 
                user_id = ?, ext_num1 = ?
            WHERE music_id = ? AND level = ?
            """,
            (
                self.play_count,
                self.achievement,
                self.combo_status,
                self.sync_status,
                self.deluxscore_max,
                self.score_rank,
                self.user_id,
                self.ext_num1,
                self.music_id,
                self.level,
            ),
        )
        conn.commit()


def parse_combo_status(fc_value):
    switcher = {"fc": 1, "fcp": 2, "ap": 3, "app": 4}
    return switcher.get(fc_value, 0)


def parse_sync_status(fs_value):
    switcher = {"sync": 5, "fs": 1, "fsp": 2, "fsd": 3, "fsdp": 4}
    return switcher.get(fs_value, 0)


def parse_achievements(achievements):
    parsed_achievements = int(10000 * achievements)
    return parsed_achievements


def save_player_scores(payload: dict, user_id, overwrite: bool = False):
    """_summary_

    Args:
        payload (dict): 用户成绩字典
        user_id (int): 用于指示 db.sqlite 中的用户
        overwrite (bool): 是否覆写（否则择优）
    """

    data = payload
    conn = sqlite3.connect(db_path)

    if overwrite:
        # 清除数据库 maimai2_user_music_detail 表中的内容
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM maimai2_user_music_detail WHERE user_id = ?", (user_id,)
        )
        conn.commit()

    with tqdm(total=len(data["records"]), desc="保存玩家成绩", unit="record") as pbar:
        for record in data["records"]:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, achievement, deluxscore_max, play_count, combo_status, sync_status FROM maimai2_user_music_detail 
                WHERE music_id = ? AND level = ? AND user_id = ?
                """,
                (record["song_id"], record["level_index"], user_id),
            )
            existing_score = cursor.fetchone()

            if existing_score and not overwrite:
                (
                    existing_id,
                    existing_achievement,
                    existing_deluxscore_max,
                    existing_play_count,
                    existing_combo_status,
                    existing_sync_status,
                ) = existing_score

                new_achievement = parse_achievements(record["achievements"])
                new_combo_status = parse_combo_status(record["fc"])
                new_sync_status = parse_sync_status(record["fs"])
                new_deluxscore_max = record["dxScore"]

                score = song_score(
                    id=existing_id,
                    music_id=record["song_id"],
                    level=record["level_index"],
                    play_count=existing_play_count,
                    achievement=max(new_achievement, existing_achievement),
                    combo_status=max(new_combo_status, existing_combo_status),
                    sync_status=max(
                        new_sync_status,
                        existing_sync_status,
                        key=lambda x: (x == 5, x),
                    ),
                    deluxscore_max=max(new_deluxscore_max, existing_deluxscore_max),
                    score_rank=0,
                    user_id=user_id,
                    ext_num1=0,
                )

                score.update_in_db(conn)
            else:
                cursor.execute(
                    """
                    SELECT MAX(id) FROM maimai2_user_music_detail
                    """
                )
                max_id = cursor.fetchone()[0]
                new_id = (max_id + 1) if max_id is not None else 1
                score = song_score(
                    id=new_id,
                    music_id=record["song_id"],
                    level=record["level_index"],
                    play_count=1,
                    achievement=parse_achievements(record["achievements"]),
                    combo_status=parse_combo_status(record["fc"]),
                    sync_status=parse_sync_status(record["fs"]),
                    deluxscore_max=record["dxScore"],
                    score_rank=0,
                    user_id=user_id,
                    ext_num1=0,
                )
                score.insert_into_db(conn)

            pbar.update(1)

    conn.close()
