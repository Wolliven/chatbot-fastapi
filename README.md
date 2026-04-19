# Chatbot API (FastAPI)

FastAPI backend for customer support and reservation flows, with LINE webhook support and a configurable LLM layer.

## Requirements

- Python 3.10+
- Virtual environment (`venv`)

## Installation

```bash
git clone https://github.com/YOUR-USERNAME/chatbot-fastapi.git
cd Proyecto_bot_api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root.

```env
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_OWNER_GROUP_ID=...

LLM_PROVIDER=gemini

GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT_SECONDS=60
```

Only the selected provider needs to be available at runtime.

## Switching LLM Providers

The application now selects the LLM provider through configuration only.

- Use `LLM_PROVIDER=gemini` for the remote Gemini API.
- Use `LLM_PROVIDER=ollama` for a local Ollama server.
- Restart the FastAPI server after changing provider settings.

No business-logic changes are required when switching providers.

## Run Locally

```bash
uvicorn app.main:app --reload --port 8000
```

## Main Endpoints

- `POST /ask`
- `POST /line/webhook`

## Development Check

```bash
python -m unittest discover -s tests -v
```
