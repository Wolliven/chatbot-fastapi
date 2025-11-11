🚀 Cómo probar el bot en local (entorno de desarrollo)
1️⃣ Activar el entorno virtual
cd C:\Users\jeric\Desktop\Proyectos\Proyecto_bot_api
venv\Scripts\activate

2️⃣ Ejecutar el servidor FastAPI
uvicorn app.main:app --reload --port 8000

3️⃣ Abrir ngrok (para exponer el puerto 8000)
ngrok http 8000


Copia la URL HTTPS que aparezca (ej. https://abcd.ngrok-free.dev)

En LINE Developers Console → Messaging API settings,
pon esa URL como Webhook:

https://abcd.ngrok-free.dev/line/webhook


Asegúrate de que “Use webhook” está activado (ON).

4️⃣ Probar el bot

Abre LINE y mándale un mensaje al bot.

Si todo está correcto, responderá según core/chatbot.py.

5️⃣ Cerrar sesión

Cuando termines de probar:

Ctrl + C en la terminal de FastAPI.

Ctrl + C en la terminal de ngrok.
(Se cierran ambos servicios.)

💾 Cómo volver a una versión anterior del proyecto en GitHub

Ver el historial de commits:

git log --oneline


(te mostrará una lista tipo a1b2c3 Fix: ajustes en chatbot.py)

Volver temporalmente a una versión anterior:

git checkout a1b2c3


(solo para inspeccionar o recuperar un archivo.)

Volver a la rama principal:

git checkout main


Si rompiste algo y quieres “retroceder” definitivamente:

git revert a1b2c3


Esto crea un nuevo commit que deshace los cambios.

🔑 Recordatorio sobre variables .env

El archivo .env nunca se sube a GitHub (por seguridad).
Si lo pierdes, crea uno nuevo con tus claves:

GEMINI_API_KEY=...
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...


Y guarda una copia aparte en un bloc de notas local.

🧠 Checklist rápido antes de cada prueba
Elemento	Verificación
.env	existe y tiene tus claves
uvicorn	corriendo sin errores
ngrok	abierto y con URL HTTPS activa
LINE webhook	actualizado con esa URL
modo descanso	desactivado mientras pruebas