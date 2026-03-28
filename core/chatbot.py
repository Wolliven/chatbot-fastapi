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
        You are a customer support assistant for the business "{client}".

        Rules:
        - Answer in the same language as the user.
        - Be polite, clear, and concise.
        - Use only the business information provided below.
        - Do not invent facts, prices, schedules, or policies.
        - If the information is missing, say you do not know.
        - If the user wants to make a reservation, do not confirm it unless the system has actually saved it.

        Business information:
        ---
        {context}
        ---

        User message:
        ---
        {question}
        ---
    """

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
            }
        )

        if hasattr(response, "text") and response.text:
            answer = response.text.strip()
        else:
            answer = "No se pudo generar una respuesta válida."

        log_conversation(
            client=client,
            question=question,
            answer=answer,
            intent="qa",
            success=True
        )
        return answer

    except Exception as e:
        print("❌ Error en ask_bot:", e)
        return f"Sorry, an internal error ocurred, please try again."
