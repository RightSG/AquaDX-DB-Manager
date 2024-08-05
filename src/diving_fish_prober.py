import json
import requests
from requests.exceptions import RequestException


class ProberAPIClient:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.network_timeout = 10
        self.client = requests.Session()
        self.jwt = ""
        self.base_url = "https://www.diving-fish.com/api/maimaidxprober"

    def login(self):
        body = {"username": self.username, "password": self.password}

        try:
            response = self.client.post(
                f"{self.base_url}/login",
                headers={"Content-Type": "application/json"},
                json=body,
                timeout=self.network_timeout,
            )
        except RequestException as e:
            raise RuntimeError("登录失败: {}".format(e))

        if response.status_code != 200:
            raise ValueError("登录凭据错误")

        self.jwt = response.cookies.get("jwt_token", "")
        self.client.cookies.set("jwt_token", self.jwt)

    def handle_request_exception(self, response, exception):
        if response is None:
            message = "Unknown error"
            status_code = "No response"
            url = "No URL"
        else:
            try:
                message = response.json().get("message", "Unknown error")
            except Exception:
                message = response.text
            status_code = response.status_code
            url = response.url

        raise RuntimeError(
            f"请求失败: {exception}, 状态码: {status_code}, URL: {url}, message: {message}"
        )

    def get_player_full_scores(self, username, password):
        if not self.jwt:
            self.username = username
            self.password = password
            self.login()

        url = f"{self.base_url}/player/records"

        try:
            response = self.client.get(url)
            response.raise_for_status()
        except RequestException as e:
            try:
                message = response.json().get("message", "Unknown error")
            except Exception:
                message = "Unknown error"
            raise RuntimeError(f"GET 请求失败: {e}, message: {message}")

        return response.json()

    def get_music_data(self):
        url = f"{self.base_url}/music_data"
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except RequestException as e:
            try:
                message = response.json().get("message", "Unknown error")
            except Exception:
                message = "Unknown error"
            raise RuntimeError(f"GET 请求失败: {e}, message: {message}")

        return response.json()

    def update_records(self, username, password, records):
        if not self.jwt:
            self.username = username
            self.password = password
            self.login()

        url = f"{self.base_url}/player/update_records"
        headers = {"Content-Type": "application/json"}

        try:
            response = self.client.post(
                url,
                headers=headers,
                json=records,
                timeout=self.network_timeout,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 500:
                print("服务器返回500错误，这可能不影响上传进行，请稍后手动检查。")
                return {
                    "status": "success",
                    "message": "服务器返回500错误，请手动检查上传结果",
                }
            else:
                self.handle_request_exception(response, e)
        except RequestException as e:
            self.handle_request_exception(response, e)

        return response.json()

    def delete_player_records(self, username, password):
        if not self.jwt:
            self.username = username
            self.password = password
            self.login()

        url = "https://www.diving-fish.com/api/maimaidxprober/player/delete_records"

        try:
            response = self.client.delete(url)
            response.raise_for_status()
        except RequestException as e:
            self.handle_request_exception(response, e)

        return response.json()


with open("adm_config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

client = ProberAPIClient()


def get_player_scores():
    full_scores = client.get_player_full_scores(config["username"], config["password"])
    return full_scores


def get_music_data():
    music_data = client.get_music_data()
    return music_data
