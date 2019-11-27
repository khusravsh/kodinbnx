import datetime
import os

import requests

from coding_tasks import task_schedule
from coding_tasks.models import Solution, Task

BOT_API_KEY = os.environ["TELEGRAM_BOT_API_KEY"]
CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
URL_BASE = f"https://api.telegram.org/bot{BOT_API_KEY}/"

SITE_URL = "https://kodingbnx.pythonanywhere.com/"
NO_TOMORROW_TASK_MESSAGE = "@asizikov @dizzy57 No task for tomorrow"
FIRST_DAY_OF_MONTH_MESSAGE = "@dizzy57 Refresh the hosting"


class TelegramApi:
    def __init__(self):
        self.session = requests.session()

    def close(self):
        self.session.close()

    def _call(self, endpoint, data):
        res = self.session.post(URL_BASE + endpoint, json=data)
        res.raise_for_status()
        return res.json()

    def send_message(self, text):
        data = {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}
        return self._call("sendMessage", data)

    def pin_message(self, message_id):
        data = {
            "chat_id": CHAT_ID,
            "message_id": message_id,
            "disable_notification": True,
        }
        return self._call("pinChatMessage", data)


class TelegramBot:
    def __init__(self):
        self.api = TelegramApi()
        self.today = task_schedule.today()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.api.close()
        return False

    def send_and_pin_task_for_today(self):
        try:
            task = Task.objects.get(date=self.today)
        except Task.DoesNotExist:
            self.api.send_message("No task for today :(")
            return

        m = self.api.send_message("\n".join((task.name, task.url, SITE_URL)))
        self.api.pin_message(m["result"]["message_id"])

    def send_solutions_for_today(self):
        text = f"Solutions:\n{SITE_URL}solutions/{self.today:%Y-%m-%d}"
        self.api.send_message(text)

    def notify_if_no_tasks_for_tomorrow(self):
        tomorrow = self.today + datetime.timedelta(days=1)
        if not Task.objects.filter(date=tomorrow):
            self.api.send_message(NO_TOMORROW_TASK_MESSAGE)

    def notify_if_first_day_of_month(self):
        if self.today.day == 1:
            self.api.send_message(FIRST_DAY_OF_MONTH_MESSAGE)

    def notify_additional_solution(self, solution: Solution):
        text = f"New solution by {solution.user.first_name}: {SITE_URL}solutions/{self.today:%Y-%m-%d}#u{solution.user.id}-1"
        self.api.send_message(text)
