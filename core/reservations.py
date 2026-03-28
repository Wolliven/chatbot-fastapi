import json
import os
from datetime import datetime
from typing import Dict, Tuple, Optional
import uuid
from core.state import get_state, update_state, clear_state

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


def is_user_in_reservation_flow(user_id: str) -> bool:
    return bool(get_state(user_id))


def start_reservation_flow_jp(user_id: str, client: str) -> str:
    update_state[user_id] = {
        "step": "ask_date",
        "data": {},
        "client": client,
    }
    return (
        "ご予約ですね。ありがとうございます！\n\n"
        "📅 ご希望の日付を教えてください。\n"
        "（例：2025-12-24）"
    )


def continue_reservation_flow_jp(user_id: str, user_text: str) -> Tuple[str, Optional[dict]]:
    """
    現在のステップに応じてユーザーの入力を処理し、
    次に送るメッセージと、オーナー通知用の予約情報(あれば)を返す。

    戻り値:
      (reply_text, reservation_dict_or_None)
    """
    state = get_state(user_id)
    if not state:
        return "すみません、もう一度メニューから「予約」を選んでください。", None

    step = state["step"]
    data = state["data"]

    # 1) 日付
    if step == "ask_date":
        data["date"] = user_text.strip()
        state["step"] = "ask_time"
        return (
            "⏰ ご希望の時間を教えてください。\n"
            "（例：19:30）"
        ), None

    # 2) 時間
    elif step == "ask_time":
        data["time"] = user_text.strip()
        state["step"] = "ask_people"
        return (
            "👥 何名様でご利用予定でしょうか？\n"
            "（例：2名）"
        ), None

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
        ), None

    # 4) 最終確認
    elif step == "confirm":
        text_norm = user_text.strip().lower()

        ok_words = ["はい", "はい。", "ok", "okです", "yes", "y", "si", "sí"]
        cancel_words = ["いいえ", "いいえ。", "no", "キャンセル"]

        # オーナー通知用の予約 dict（OK のときだけ埋める）
        if text_norm in ok_words:
            client_name = state["client"]

            reservation = {
                "id": "R" + uuid.uuid4().hex[:8],
                "date": data.get("date"),
                "time": data.get("time"),
                "people": data.get("people"),
                "source": "line",
                "status": "pending",
                "user_id": user_id,
                "client": client_name,
            }

            # JSON に保存
            save_reservation(client_name, reservation)
            # 状態クリア
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
