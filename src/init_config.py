import os
import json

CONFIG_FILE = "adm_config.json"
README_FILE = "README.txt"


def create_readme_if_not_exists():
    readme_path = "README.txt"
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(
                r"""使用本工具进行 AquaDX 本地服务器数据库与 diving-fish 数据库的交互，您需要在生成的 config.json 中填入以下数据：

"username":"your_diving_fish_username"
"password": "your_diving_fish_password"
请将右侧双引号内的内容替换为实际的 diving-fish 用户名和密码

"aqua_path": "D:\\aqua-0.0.46-RELEASE"（示例）
aqua 路径的填写需要注意以下几点：
1.该路径下您应当能看到 aqua.jar, data 文件夹等其他内容
2.反斜杠需要使用双反斜杠防止识别错误

脚本运行前您需要至少先进行一局游戏并成功保存数据。如果仍然出错，您可能需要检查 aqua_path 下的 data 文件夹内是否生成了 db.sqlite

如果您希望将 diving-fish 上的数据保存至 AquaDX 本地服务器，在程序提示同步完成后，游戏刷卡界面可能不会立即显示同步后的 rating 信息，这是正常现象。
您只需要继续点击数次下一步，在进入选歌界面之前就会正常计算同步后的 rating 。您只需要进行一次正常游玩并保存数据之后即可在刷卡界面正常显示。
另外同步之后第一次游玩可能会再次出现新手教程的提示，这也是正常现象，跳过即可。
"""
            )
            print(f"已创建 {README_FILE} 文件。")


def create_adm_config_if_not_exists():
    if not os.path.exists(CONFIG_FILE):
        config_data = {"username": "", "password": "", "aqua_path": ""}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        print(f"已创建默认配置文件 {CONFIG_FILE}。初次运行，请先填写相关信息。")
        return True
    return False
