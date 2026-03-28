import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from core.utils import log_conversation

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def configure_gemini() -> None:
    # Cargar variables del entorno y configurar API
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")

    # fuerza limpieza de credenciales previas (importante en Windows)
    os.environ.pop("GOOGLE_API_KEY", None)
    os.environ["GOOGLE_API_KEY"] = key
    genai.configure(api_key=key)

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


def ask_bot(client: str, question: str) -> str:
    """
    Genera una respuesta usando los datos del cliente indicado.
    (Flujo estable actual; la detección de reserva está preparada pero no activa.)
    """
    try:
        context = load_information(client)

        prompt = f"""
Eres un asistente para el negocio '{client}'.

Usa solo la siguiente información para responder con precisión.
Si no hay datos relevantes, responde cortésmente que no lo sabes.

Información del negocio:
{context}

Pregunta del cliente:
{question}

Always reply in the same language as the user's message. If they text in japanese, reply in japanese.
"""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            answer = response.text.strip()
        else:
            answer = "No se pudo generar una respuesta válida."

        log_conversation(f"[{client}] {question}", answer)
        return answer

    except Exception as e:
        print("❌ Error en ask_bot:", e)
        return f"Error interno: {e}"
