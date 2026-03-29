import os
import hmac
import hashlib
import base64
import json

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from core.chatbot import ask_bot, configure_gemini
from core.utils import reset_log_if_needed
from core.reservations import (
    start_reservation_flow,
    continue_reservation_flow,
    is_user_in_reservation_flow,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    configure_gemini()
    reset_log_if_needed()
    yield
    print("App shutting down")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    client: str
    question: str

@app.post("/ask")
async def ask(data: Question):
    answer = ask_bot(data.client, data.question)
    return {"answer": answer}


# ======================================================
#  ✅ Añade esto para conectar con LINE
# ======================================================

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_OWNER_GROUP_ID = os.getenv("LINE_OWNER_GROUP_ID", "")
RESERVATION_TRIGGER = "予約"  # ← pon aquí EXACTAMENTE el texto del botón

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

@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")
    if not verify_line_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)
    events = data.get("events", [])

    async with httpx.AsyncClient() as client:
        for event in events:
            #Cada vez que se quiera añadir un grupo, poner aquí esta línea
            #print(json.dumps(event, ensure_ascii=False, indent=2))
            if event.get("type") == "message" and event["message"]["type"] == "text":
                reply_token = event["replyToken"]
                user_text = event["message"]["text"]
                # userId を取得（1:1チャット前提）
                user_id = event["source"].get("userId")

                # Por ahora, el cliente lo fijamos a gyudon_shop
                client_name = "gyudon_shop"

                # Decidimos qué responder
                # 1) Si el texto viene del botón de reserva → iniciar flujo
                if user_text.strip() == RESERVATION_TRIGGER and user_id:
                    reply_text = start_reservation_flow(user_id, client_name)

                # 2) Si el usuario ya está en el flujo de reserva → continuar
                elif user_id and is_user_in_reservation_flow(user_id):
                    reply_text, reservation = continue_reservation_flow(user_id, user_text)

                    # Si se ha creado una reserva nueva (confirmada), notificamos al dueño
                    if reservation is not None:
                        try:
                            await notify_owner_of_reservation(client, reservation)
                        except Exception as e:
                            print("Error enviando notificación al dueño:", e)


                # 3) Si no es reserva → chatbot normal
                else:
                    try:
                        answer = ask_bot(client_name, user_text)
                    except Exception as e:
                        print("Error en ask_bot:", e)
                        answer = "申し訳ありません。内部エラーが発生しました。"
                    reply_text = answer

                # Enviar respuesta a LINE
                response = await client.post(
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


    return {"status": "ok"}
