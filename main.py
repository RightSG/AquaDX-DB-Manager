import os
import json
import shutil
from src.init_config import create_adm_config_if_not_exists, create_readme_if_not_exists

CONFIG_FILE = "adm_config.json"
README_FILE = "README.txt"
VERSION = "1.0.0"


def wait_for_exit():
    input("请按任意键退出...")


def check_files():
    create_readme_if_not_exists()
    if create_adm_config_if_not_exists():
        return False

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    db_path = os.path.join(config["aqua_path"], "data", "db.sqlite")
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，请检查 aqua_path 配置。")
        wait_for_exit()
        return False
    return True


print(f"当前版本: {VERSION}")


# 检查和创建配置文件后导入其他模块
if not check_files():
    wait_for_exit()
    exit()

from src.diving_fish_prober import ProberAPIClient, get_player_scores
from src.diving_fish_to_aquadx import save_player_scores
from src.aquadx_to_diving_fish import aquadx_data_upload
from src.aquadx_get_user import get_user


def save_game(config):
    db_path = os.path.join(config["aqua_path"], "data", "db.sqlite")
    save_files = [
        f for f in os.listdir() if f.startswith("save") and f.endswith(".sqlite")
    ]

    # 找到第一个可用的存档位
    save_indices = sorted(int(f[4:-7]) for f in save_files)
    save_index = 1
    for index in save_indices:
        if save_index < index:
            break
        save_index += 1

    save_file_name = f"save{save_index}.sqlite"

    shutil.copy(db_path, save_file_name)
    print(f"存档已保存为 {save_file_name}")


def load_game(config):
    db_path = os.path.join(config["aqua_path"], "data", "db.sqlite")
    save_files = [
        f for f in os.listdir() if f.startswith("save") and f.endswith(".sqlite")
    ]

    if not save_files:
        print("没有找到任何存档文件。")
        return

    print("可用的存档文件：")
    for i, save_file in enumerate(save_files, 1):
        # 临时复制存档文件以读取用户信息
        temp_db_path = os.path.join(config["aqua_path"], "data", f"temp_{save_file}")
        shutil.copy(save_file, temp_db_path)

        users = get_user(temp_db_path)
        if users:
            user_info = "\n".join(
                [
                    f"user_id: {user['id']}, user_name: {user['user_name']}, rating: {user['player_rating']}"
                    for user in users
                ]
            )
        else:
            user_info = "没有查询到玩家信息"

        print(f"{i}. {save_file} - {user_info}")

        # 删除临时文件
        os.remove(temp_db_path)

    choice = int(input("请选择要读取的存档编号: "))
    if choice < 1 or choice > len(save_files):
        print("无效的选择。")
        return

    selected_save_file = save_files[choice - 1]

    shutil.copy(selected_save_file, db_path)
    print(f"已加载存档 {selected_save_file}")


def main():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if not config["username"] or not config["password"] or not config["aqua_path"]:
        print("请先填写config.json文件中的配置信息。")
        wait_for_exit()
        return

    client = ProberAPIClient()
    client.username = config["username"]
    client.password = config["password"]
    try:
        client.login()
    except Exception as e:
        print(
            f"diving-fish 登录凭证验证失败，请检查 config.json 中的信息是否正确输入: {e}"
        )
        wait_for_exit()
        return
    print("验证 diving-fish 账号信息成功。")

    users = get_user()
    if not users:
        print(
            "没有查询到 AquaDX 数据库中的玩家信息。请先进行至少一局游戏并成功保存记录。"
        )
        wait_for_exit()
        return

    user_info = "\n".join(
        [
            f"user_id: {user['id']}, user_name: {user['user_name']}, rating: {user['player_rating']}"
            for user in users
        ]
    )
    print(f"查询到 aquadx 中的玩家信息:\n{user_info}")
    user_id = int(input("请选择要操作的玩家数据: "))

    # 选择菜单
    print("请选择要执行的操作：")
    print("1. 同步 diving-fish 玩家成绩至 AquaDX")
    print("2. 上传 AquaDX 数据至 diving-fish")
    print("3. 保存当前 AquaDX 数据存档")
    print("4. 读取已保存的存档数据覆盖 AquaDX 数据")
    choice = input("请输入操作编号 (1, 2, 3 或 4): ")

    if choice not in ["1", "2", "3", "4"]:
        print("无效的选择。")
        wait_for_exit()
        return

    if choice in ["1", "2"]:
        overwrite_choice = input("是否覆盖已有成绩(否则择优保存)(y/n): ")
        overwrite = overwrite_choice.lower() == "y"

        if overwrite:
            confirm_choice = input("覆盖成绩会清除现有成绩，是否确定？(y/n): ")
            if confirm_choice.lower() != "y":
                print("操作已取消。")
                wait_for_exit()
                return
    else:
        overwrite = False

    if choice == "1":
        # 同步 diving-fish 玩家成绩至 AquaDX
        scores = get_player_scores()
        save_player_scores(scores, user_id, overwrite=overwrite)
        print("同步 diving-fish 玩家成绩至 AquaDX 成功")
    elif choice == "2":
        # 上传 AquaDX 数据到 diving-fish
        response = aquadx_data_upload(user_id=user_id, overwrite=overwrite)
        if response.get("message") == "更新成功":
            print("上传 AquaDX 数据到 diving-fish 成功")
        else:
            print(
                f"上传出现异常，状态码: {response.get('status_code')}, 信息: {response.get('message')}"
            )
    elif choice == "3":
        # 保存存档
        save_game(config)
    elif choice == "4":
        # 读取存档
        load_game(config)

    wait_for_exit()


if __name__ == "__main__":
    main()
