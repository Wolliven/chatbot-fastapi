# Desarrollo local

## 1. Activar el entorno virtual

```powershell
cd C:\Users\jeric\Desktop\Proyectos\Proyecto_bot_api
venv\Scripts\activate
```

## 2. Variables `.env`

Crea o actualiza `.env` con estas claves:

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

Notas:

- Si usas `LLM_PROVIDER=gemini`, necesitas `GEMINI_API_KEY`.
- Si usas `LLM_PROVIDER=ollama`, necesitas tener Ollama corriendo en la URL configurada.
- Cambiar el proveedor solo requiere cambiar variables y reiniciar el servidor.

## 3. Ejecutar FastAPI

```powershell
uvicorn app.main:app --reload --port 8000
```

## 4. Exponer el puerto con ngrok

```powershell
./ngrok http 8000
```

Copia la URL HTTPS y configuralo en LINE Developers Console:

```text
https://TU-URL.ngrok-free.dev/line/webhook
```

Activa `Use webhook`.

## 5. Probar el bot

- Abre LINE y envia un mensaje al bot.
- Tambien puedes probar el endpoint local:

```powershell
curl -X POST http://127.0.0.1:8000/ask `
  -H "Content-Type: application/json" `
  -d "{\"client\":\"Misky\",\"question\":\"Hello\"}"
```

## 6. Verificacion rapida

```powershell
python -m unittest discover -s tests -v
```

## 7. Cerrar la sesion

- `Ctrl + C` en la terminal de FastAPI.
- `Ctrl + C` en la terminal de ngrok.
