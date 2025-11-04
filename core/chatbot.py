import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from core.utils import log_conversation

# Cargar variables del entorno y configurar API
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def detect_language(text: str) -> str:
    """Detección mínima de idioma (es/en/ja)."""
    if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', text):
        return "ja"
    if len(re.findall(r'[a-zA-Z]', text)) / max(len(text), 1) > 0.5:
        return "en"
    return "es"


def load_information(client: str) -> str:
    """Carga los archivos de datos (menu, schedule, faq) del cliente indicado."""
    base_path = f"clients/{client}/data"
    if not os.path.exists(base_path):
        return f"No se encontró información para el cliente '{client}'."

    docs = []
    for filename in os.listdir(base_path):
        if filename.endswith(".txt"):
            path = os.path.join(base_path, filename)
            with open(path, "r", encoding="utf-8") as f:
                docs.append(f"{filename.replace('.txt', '').capitalize()}:\n{f.read()}\n")
    return "\n".join(docs)


def ask_bot(client: str, question: str) -> str:
    """Genera una respuesta usando los datos del cliente indicado."""
    try:
        context = load_information(client)

        # Detección de idioma
        lang = detect_language(question)
        lang_instruction = {
            "es": "Responde en español, de forma natural y amable.",
            "en": "Answer naturally in English, friendly and clear.",
            "ja": "日本語で自然に丁寧に答えてください。",
        }.get(lang, "Responde en español.")

        prompt = f"""
Eres un asistente para el negocio '{client}'.
{lang_instruction}

Usa solo la siguiente información para responder con precisión.
Si no hay datos relevantes, responde cortésmente que no lo sabes.

Información del negocio:
{context}

Pregunta del cliente:
{question}
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
