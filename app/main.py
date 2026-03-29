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
    handle_line_event
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

            await handle_line_event(
                http_client=http_client,
                event=event,
                client_name="gyudon_shop",
            )


    return {"status": "ok"}
