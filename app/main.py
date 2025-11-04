from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.chatbot import ask_bot
from core.utils import reset_log_if_needed

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
