from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.chatbot import ask_bot
from core.utils import reset_log_if_needed
import os, hmac, hashlib, base64, json, httpx
from core.reservations import (
    start_reservation_flow_jp,
    continue_reservation_flow_jp,
    is_user_in_reservation_flow,
)


# Reiniciar log al arrancar el servidor
reset_log_if_needed()

app = FastAPI()

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
RESERVATION_TRIGGER = "予約"  # ← pon aquí EXACTAMENTE el texto del botón


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
                    reply_text = start_reservation_flow_jp(user_id, client_name)

                # 2) Si el usuario ya está en el flujo de reserva → continuar
                elif user_id and is_user_in_reservation_flow(user_id):
                    reply_text = continue_reservation_flow_jp(user_id, user_text)

                # 3) Si no es reserva → chatbot normal
                else:
                    try:
                        answer = ask_bot(client_name, user_text)
                    except Exception as e:
                        print("Error en ask_bot:", e)
                        answer = "申し訳ありません。内部エラーが発生しました。"
                    reply_text = answer

                # Enviar respuesta a LINE
                await client.post(
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


    return {"status": "ok"}
