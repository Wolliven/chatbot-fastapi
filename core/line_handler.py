
import hmac
import hashlib
import base64
from typing import Optional

from core.chatbot import process_message
from core.reservations import (
    start_reservation_flow,
    continue_reservation_flow,
    is_user_in_reservation_flow,
)
from core.config import LINE_OWNER_GROUP_ID, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, RESERVATION_TRIGGER

async def notify_owner_of_reservation(http_client, reservation: dict):
    """
    Envía un push message al grupo del propietario con la info de la reserva.
    """
    if not LINE_OWNER_GROUP_ID:
        print("LINE_OWNER_GROUP_ID no está configurado; no se enviará notificación al dueño.")
        return

    text = (
        "📩 新しい予約リクエストがあります\n"
        f"店舗: {reservation.get('client', '不明')}\n"
        f"予約ID: {reservation.get('id')}\n"
        f"日付: {reservation.get('date')}\n"
        f"時間: {reservation.get('time')}\n"
        f"人数: {reservation.get('people')}\n"
        f"名前: {reservation.get('name')}\n"
        f"ユーザーID: {reservation.get('user_id')}\n"
        "\n問題がある場合は、お客様にご連絡ください。"
    )

    response = await http_client.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "to": LINE_OWNER_GROUP_ID,
            "messages": [{"type": "text", "text": text}],
        },
    )
    response.raise_for_status()


def verify_line_signature(body: bytes, signature: str) -> bool:
    mac = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode()
    return hmac.compare_digest(expected, signature)


def parse_line_text_event(event: dict) -> dict | None:
    """
    Extract the relevant data from a LINE text message event.
    Return None if the event is not a text message.
    """
    if event.get("type") != "message":
        return None

    message = event.get("message", {})
    if message.get("type") != "text":
        return None

    source = event.get("source", {})

    return {
        "reply_token": event.get("replyToken"),
        "user_text": message.get("text", ""),
        "user_id": source.get("userId"),
    }


def process_line_message(client_name: str, client_type: str, user_id: str | None, user_text: str) -> tuple[str, Optional[dict]]:
    """
    Decide how to handle an incoming LINE text message.
    Returns:
        (reply_text, reservation_or_none)
    """
    if user_id and is_user_in_reservation_flow(user_id):
        return continue_reservation_flow(user_id, user_text, client_type)

    try:
        decision = process_message(client_name, user_text)
    except Exception as e:
        print("Error in process_message:", e)
        return "申し訳ありません。内部エラーが発生しました。", None

    if decision.action == "reservation" and user_id:
        reply_text = start_reservation_flow(user_id, client_name, client_type)
        return reply_text, None

    if decision.action == "chat" and decision.reply_text:
        return decision.reply_text, None

    return "申し訳ありません。うまく処理できませんでした。もう一度お試しください。", None

async def handle_line_event(http_client, event: dict, client_name: str, client_type: str = "restaurant") -> None:
    """
    Handle one LINE event if it is a text message.
    Ignore non-text events.
    """
    parsed_event = parse_line_text_event(event)
    if parsed_event is None:
        return

    reply_token = parsed_event["reply_token"]
    user_text = parsed_event["user_text"]
    user_id = parsed_event["user_id"]

    reply_text, reservation = process_line_message(
        client_name=client_name,
        client_type=client_type,
        user_id=user_id,
        user_text=user_text,
    )

    if reservation is not None:
        try:
            await notify_owner_of_reservation(http_client, reservation)
        except Exception as e:
            print("Error sending notification to owner:", e)

    await send_line_reply(http_client, reply_token, reply_text)

async def send_line_reply(http_client, reply_token: str, reply_text: str):
    """
    Send a reply message back to the LINE user.
    """
    response = await http_client.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": reply_text}],
        },
    )
    response.raise_for_status()