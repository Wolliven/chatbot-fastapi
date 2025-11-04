import datetime
import os

SESSION_STARTED = False  # bandera para evitar múltiples reinicios


def reset_log_if_needed():
    """Borra el log solo una vez por sesión (cuando se arranca el servidor)."""
    global SESSION_STARTED
    if SESSION_STARTED:
        return  # ya fue reiniciado

    os.makedirs("logs", exist_ok=True)
    with open("logs/conversations.txt", "w", encoding="utf-8") as f:
        f.write(f"[Session started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n\n")

    SESSION_STARTED = True


def log_conversation(question: str, answer: str):
    """Guarda cada interacción en logs/conversations.txt"""
    os.makedirs("logs", exist_ok=True)
    with open("logs/conversations.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}]\nQ: {question}\nA: {answer}\n\n")

import re

def detect_language(text: str) -> str:
    """Detección mínima del idioma (en/es/ja)."""
    # japonés
    if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', text):
        return "ja"
    # inglés (si más del 50% de las palabras son ASCII)
    if len(re.findall(r'[a-zA-Z]', text)) / max(len(text), 1) > 0.5:
        return "en"
    return "es"
