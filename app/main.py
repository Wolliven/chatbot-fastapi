import json

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from core.chatbot import ask_bot, configure_gemini
from core.utils import reset_log_if_needed
from core.line_handler import (
    verify_line_signature,
    parse_line_text_event,
    process_line_message,
    notify_owner_of_reservation,
    send_line_reply,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-line-signature", "")
    if not verify_line_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)
    events = data.get("events", [])

    async with httpx.AsyncClient() as http_client:
        for event in events:
            # Print the event when debugging new LINE event types or chat sources.
            # print(json.dumps(event, ensure_ascii=False, indent=2))

            parsed_event = parse_line_text_event(event)
            if parsed_event is None:
                continue

            reply_token = parsed_event["reply_token"]
            user_text = parsed_event["user_text"]
            user_id = parsed_event["user_id"]

            # For now, keep the client fixed to gyudon_shop.
            client_name = "gyudon_shop"

            reply_text, reservation = process_line_message(
                client_name=client_name,
                user_id=user_id,
                user_text=user_text,
            )

            if reservation is not None:
                try:
                    await notify_owner_of_reservation(http_client, reservation)
                except Exception as e:
                    print("Error sending notification to owner:", e)

            await send_line_reply(http_client, reply_token, reply_text)


    return {"status": "ok"}
