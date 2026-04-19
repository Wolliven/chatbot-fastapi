import json
import os
import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ValidationError
from zoneinfo import ZoneInfo

from core.llm import get_llm_client
from core.utils import log_conversation

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ReservationData(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    people: Optional[int] = None
    name: Optional[str] = None


class MessageDecision(BaseModel):
    action: Literal["chat", "reservation"]
    reply_text: Optional[str] = None
    reservation: Optional[ReservationData] = None


def load_information(client: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", client):
        raise ValueError("Invalid client name")

    base_path = os.path.join(BASE_DIR, "clients", client, "data")
    if not os.path.isdir(base_path):
        raise FileNotFoundError(f"Client data folder not found for '{client}'")

    docs = []
    for filename in sorted(os.listdir(base_path)):
        if filename.endswith(".txt"):
            path = os.path.join(base_path, filename)
            with open(path, "r", encoding="utf-8") as f:
                title = filename.replace(".txt", "").capitalize()
                docs.append(f"{title}:\n{f.read().strip()}")

    return "\n\n".join(docs)


def build_prompt(client: str, context: str, user_message: str) -> str:
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()

    return f"""
You are a customer support assistant for the business "{client}".

Today's date in Japan is: {today}

You must decide whether the user message is:
1. a normal customer support chat message
2. a reservation-related message

Return ONLY valid JSON.
Do not use markdown.
Do not add explanations.
Do not invent missing information.

Use exactly this schema:
{{
  "action": "chat" or "reservation",
  "reply_text": "string or null",
  "reservation": {{
    "date": "YYYY-MM-DD" or null,
    "time": "HH:MM" or null,
    "people": integer or null,
    "name": "string or null"
  }} or null
}}

Rules:
- Answer in the same language as the user.
- Be polite, clear, and concise.
- Use only the business information provided below.
- Do not invent facts, prices, schedules, or policies.
- If the information is missing, say you do not know.
- If the user wants to make, change, or ask for a reservation or table booking, set action to "reservation".
- If action is "reservation", set reply_text to null.
- If action is "chat", fill reply_text with the message to send to the user.
- Never claim a reservation is confirmed unless the system has actually saved it.
- Extract reservation fields only if they are explicitly present or clearly inferable.
- Convert relative dates like "tomorrow" into YYYY-MM-DD using today's date.
- Convert times into 24-hour HH:MM format when possible.

Business information:
---
{context}
---

User message:
---
{user_message}
---
""".strip()


def process_message(client: str, user_message: str) -> MessageDecision:
    """
    Process one user message with a single LLM call.

    Returns:
        MessageDecision:
        - action="chat" with reply_text
        - action="reservation" with extracted reservation fields
    """
    try:
        context = load_information(client)
        prompt = build_prompt(client=client, context=context, user_message=user_message)
        raw_text = get_llm_client().generate(
            prompt,
            temperature=0.2,
            json_mode=True,
        )
        data = json.loads(raw_text)
        decision = MessageDecision.model_validate(data)

        log_conversation(
            client=client,
            question=user_message,
            answer=decision.model_dump_json(),
            intent=decision.action,
            success=True,
        )
        return decision

    except (json.JSONDecodeError, ValidationError) as e:
        print("Structured output error in process_message:", e)
        log_conversation(
            client=client,
            question=user_message,
            answer="structured_output_error",
            intent="unknown",
            success=False,
        )
        return MessageDecision(
            action="chat",
            reply_text="Sorry, I could not process that properly. Please try again.",
            reservation=None,
        )

    except Exception as e:
        print("Error in process_message:", e)
        log_conversation(
            client=client,
            question=user_message,
            answer="internal_error",
            intent="unknown",
            success=False,
        )
        return MessageDecision(
            action="chat",
            reply_text="Sorry, an internal error occurred. Please try again.",
            reservation=None,
        )


def ask_bot(client: str, question: str) -> str:
    """
    Backward-compatible wrapper.
    Use process_message() for the new structured flow.
    """
    decision = process_message(client, question)

    if decision.action == "chat" and decision.reply_text:
        return decision.reply_text

    return "I can help with your reservation. Please provide the date, time, and number of people."
