# app/core/reservations.py
import json
import os
from datetime import datetime

def save_reservation(client: str, reservation: dict):
    """Guarda la reserva en clients/<client>/data/reservations.json"""
    base_path = f"clients/{client}/data"
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, "reservations.json")

    # Cargar reservas previas
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    reservation["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.append(reservation)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# app/core/reservations.py
import json
import os
from datetime import datetime
from typing import Dict

def save_reservation(client: str, reservation: dict):
    """Guarda la reserva en clients/<client>/data/reservations.json"""
    base_path = f"clients/{client}/data"
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, "reservations.json")

    # Cargar reservas previas
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    reservation["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.append(reservation)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==========================================
#   Estado y flujo de reservas (LINE)
# ==========================================

# user_id ごとの予約フローの状態を保存
# { user_id: { "step": "ask_date" | "ask_time" | "ask_people" | "confirm",
#              "data": {...},
#              "client": "gyudon_shop" } }
user_states: Dict[str, dict] = {}


def is_user_in_reservation_flow(user_id: str) -> bool:
    return user_id in user_states


def start_reservation_flow_jp(user_id: str, client: str) -> str:
    """
    予約フローを開始して、最初のメッセージ（質問）を返す。
    """
    user_states[user_id] = {
        "step": "ask_date",
        "data": {},
        "client": client,
    }
    return (
        "ご予約ですね。ありがとうございます！\n\n"
        "📅 ご希望の日付を教えてください。\n"
        "（例：2025-12-24）"
    )


# app/core/reservations.py
import json
import os
from datetime import datetime
from typing import Dict

def save_reservation(client: str, reservation: dict):
    """Guarda la reserva en clients/<client>/data/reservations.json"""
    base_path = f"clients/{client}/data"
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, "reservations.json")

    # Cargar reservas previas
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    reservation["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.append(reservation)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==========================================
#   Estado y flujo de reservas (LINE)
# ==========================================

# user_id ごとの予約フローの状態を保存
# { user_id: { "step": "ask_date" | "ask_time" | "ask_people" | "confirm",
#              "data": {...},
#              "client": "gyudon_shop" } }
user_states: Dict[str, dict] = {}


def is_user_in_reservation_flow(user_id: str) -> bool:
    return user_id in user_states


def start_reservation_flow_jp(user_id: str, client: str) -> str:
    """
    予約フローを開始して、最初のメッセージ（質問）を返す。
    """
    user_states[user_id] = {
        "step": "ask_date",
        "data": {},
        "client": client,
    }
    return (
        "ご予約ですね。ありがとうございます！\n\n"
        "📅 ご希望の日付を教えてください。\n"
        "（例：2025-12-24）"
    )


def continue_reservation_flow_jp(user_id: str, user_text: str) -> str:
    """
    現在のステップに応じてユーザーの入力を処理し、
    次に送るメッセージを返す。
    """
    state = user_states.get(user_id)
    if not state:
        # 何かの理由で状態が消えた場合、安全に終了
        return "すみません、もう一度メニューから「予約」を選んでください。"

    step = state["step"]
    data = state["data"]

    # 1) 日付
    if step == "ask_date":
        data["date"] = user_text.strip()
        state["step"] = "ask_time"
        return (
            "⏰ ご希望の時間を教えてください。\n"
            "（例：19:30）"
        )

    # 2) 時間
    elif step == "ask_time":
        data["time"] = user_text.strip()
        state["step"] = "ask_people"
        return (
            "👥 何名様でご利用予定でしょうか？\n"
            "（例：2名）"
        )

    # 3) 人数
    elif step == "ask_people":
        data["people"] = user_text.strip()
        state["step"] = "confirm"

        return (
            "以下の内容でご予約をお預かりしてもよろしいですか？\n\n"
            f"📅 日付: {data['date']}\n"
            f"⏰ 時間: {data['time']}\n"
            f"👥 人数: {data['people']}\n\n"
            "問題なければ「はい」と返信してください。\n"
            "キャンセルする場合は「いいえ」と送ってください。"
        )

    # 4) 最終確認
    elif step == "confirm":
        text_norm = user_text.strip().lower()

        # OK パターン（日本語＋ちょっと英語/スペイン語も許可）
        ok_words = ["はい", "はい。", "ok", "okです", "yes", "y", "si", "sí"]
        cancel_words = ["いいえ", "いいえ。", "no", "キャンセル"]

        if text_norm in ok_words:
            client_name = state["client"]
            reservation = {
                "date": data.get("date"),
                "time": data.get("time"),
                "people": data.get("people"),
                "source": "line",
                "status": "pending",
            }
            # JSON に保存
            save_reservation(client_name, reservation)
            # 状態クリア
            del user_states[user_id]

            return (
                "✅ ご予約内容をお預かりしました。\n"
                "ありがとうございました。\n"
                "お店から確認の連絡がある場合があります。"
            )

        elif text_norm in cancel_words:
            del user_states[user_id]
            return (
                "❌ ご予約をキャンセルしました。\n"
                "また必要であればメニューからもう一度「予約」をお選びください。"
            )

        else:
            return "「はい」または「いいえ」でお答えください。"

    # 想定外ステップ
    else:
        del user_states[user_id]
        return "すみません、エラーが発生しました。もう一度メニューから「予約」を選んでください。"
