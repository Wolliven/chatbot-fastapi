import json
import os
from datetime import datetime
from typing import Tuple, Optional
import uuid
from core.state import get_state, update_state, clear_state
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def save_reservation(client: str, reservation: dict):
    """Save a reservation to clients/<client>/data/reservations.json"""
    base_path = os.path.join(BASE_DIR, "clients", client, "data")
    if not os.path.isdir(base_path):
        raise FileNotFoundError(f"Client data folder not found for '{client}'")
    file_path = os.path.join(base_path, "reservations.json")

    # Load previous reservations
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                reservation_data = json.load(f)
            except json.JSONDecodeError:
                reservation_data = []
    else:
        reservation_data = []

    reservation["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reservation_data.append(reservation)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(reservation_data, f, ensure_ascii=False, indent=2)


# ==========================================
#   Reservation state and flow (LINE)
# ==========================================


def is_user_in_reservation_flow(user_id: str) -> bool:
    return bool(get_state(user_id))

def is_valid_date(text: str) -> bool:
    try:
        datetime.strptime(text.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_valid_time(text: str) -> bool:
    try:
        datetime.strptime(text.strip(), "%H:%M")
        return True
    except ValueError:
        return False

def parse_people_count(text: str) -> Optional[int]:
    match = re.search(r"\d+", text)
    if not match:
        return None

    people = int(match.group())
    if people <= 0:
        return None
    return people

def start_reservation_flow(user_id: str, client: str, client_type: str = "restaurant") -> str:
    update_state(user_id, {
        "step": "ask_date",
        "reservation_data": {},
        "client": client,
    })
    return (
        "ご予約ですね。ありがとうございます！\n\n"
        "📅 ご希望の日付を教えてください。\n"
        "（例：2025-12-24）"
    )


def continue_reservation_flow(user_id: str, user_text: str, client_type: str = "restaurant") -> Tuple[str, Optional[dict]]:
    """
    Handles current state and user and takes date, time, number of people, name and confirmation.
    """
    state = get_state(user_id)
    if not state:
        return "すみません、もう一度メニューから「予約」を選んでください。", None

    step = state["step"]
    reservation_data = state["reservation_data"]

    # 1) Date
    if step == "ask_date":
        date_text = user_text.strip()
        if not is_valid_date(date_text):
            return "日付は YYYY-MM-DD の形式で入力してください。\n（例：2025-12-24）", None
        reservation_data["date"] = date_text
        state["step"] = "ask_time"
        return (
            "⏰ ご希望の時間を教えてください。\n"
            "（例：19:30）"
        ), None

    # 2) Time
    elif step == "ask_time":
        time_text = user_text.strip()
        if not is_valid_time(time_text):
            return "時間は HH:MM の形式で入力してください。\n（例：19:30）", None
        reservation_data["time"] = time_text
        if client_type == "restaurant":
            state["step"] = "ask_people"
            return (
                "👥 何名様でご利用予定でしょうか？\n"
                "（例：2名）"
            ), None
        elif client_type == "salon":
            state["step"] = "ask_name"
            return (
            "👤 お名前をお伺いしてもよろしいでしょうか？\n"
            "（例：山田 太郎）"
            ), None


    # 3) Number of people
    elif step == "ask_people":
        people_text = user_text.strip()
        people_count = parse_people_count(people_text)
        if people_count is None:
            return "人数は 数の形式で入力してください。\n（例：2名）", None
        reservation_data["people"] = people_count
        state["step"] = "ask_name"
        return (
            "👤 お名前をお伺いしてもよろしいでしょうか？\n"
            "（例：山田 太郎）"
        ), None
    
    # 4) Name
    elif step == "ask_name":
        reservation_data["name"] = user_text.strip()
        state["step"] = "confirm"

        people_line = (
            f"👥 人数: {reservation_data['people']}\n"
            if reservation_data.get("people")
            else ""
        )

        return (
            "以下の内容でご予約をお預かりしてもよろしいですか？\n\n"
            f"📅 日付: {reservation_data['date']}\n"
            f"⏰ 時間: {reservation_data['time']}\n"
            f"{people_line}"
            f"👤 名前: {reservation_data['name']}\n\n"
            "問題なければ「はい」と返信してください。\n"
            "キャンセルする場合は「いいえ」と送ってください。"
        ), None

    # 5) Last confirmation
    elif step == "confirm":
        text_norm = user_text.strip().lower()

        ok_words = ["はい", "はい。", "ok", "okです", "yes", "y", "si", "sí"]
        cancel_words = ["いいえ", "いいえ。", "no", "キャンセル"]

        # Create reservation object
        if text_norm in ok_words:
            client_name = state["client"]

            reservation = {
                "id": "R" + uuid.uuid4().hex[:8],
                "date": reservation_data.get("date"),
                "time": reservation_data.get("time"),
                "people": reservation_data.get("people"),
                "name": reservation_data.get("name"),
                "source": "line",
                "status": "pending",
                "user_id": user_id,
                "client": client_name,
            }

            # Save JSON
            save_reservation(client_name, reservation)
            # Clear state
            clear_state(user_id)

            reply_text = (
                "✅ ご予約内容をお預かりしました。\n"
                "ありがとうございました。\n"
                "お店から確認の連絡がある場合があります。"
            )
            return reply_text, reservation

        elif text_norm in cancel_words:
            clear_state(user_id)
            reply_text = (
                "❌ ご予約をキャンセルしました。\n"
                "また必要であればメニューからもう一度「予約」をお選びください。"
            )
            return reply_text, None

        else:
            return "「はい」または「いいえ」でお答えください。", None

    else:
        clear_state(user_id)
        return "すみません、エラーが発生しました。もう一度メニューから「予約」を選んでください。", None
