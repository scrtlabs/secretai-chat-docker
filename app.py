import os
import json
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from secret_ai_sdk.secret import Secret
from secret_ai_sdk.secret_ai import ChatSecret

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# history under data/history.json
os.makedirs("data", exist_ok=True)
HISTORY_PATH = os.path.join("data", "history.json")
if not os.path.exists(HISTORY_PATH):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

@app.get("/history.json")
async def get_history():
    return FileResponse(HISTORY_PATH, media_type="application/json")

@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Load API key
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("Set API_KEY environment variable")

os.environ["SECRET_AI_API_KEY"] = API_KEY
secret_client = Secret()
models = secret_client.get_models()
MODEL = models[0]
urls = secret_client.get_urls(model=MODEL)
BASE_URL = urls[0]

llm = ChatSecret(base_url=BASE_URL, model=MODEL, temperature=1.0)

@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    # load history from data/history.json
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)

    try:
        while True:
            user_message = await websocket.receive_text()
            history.append(["user", user_message])
            history.append(["assistant", ""])  # placeholder

            prompt = [{"role": r, "content": c} for r, c in history]
            gen = llm.stream(prompt)
            full_response = ""

            loop = asyncio.get_event_loop()

            # safe "next" wrapper
            def safe_next():
                try:
                    return next(gen)
                except StopIteration:
                    return None

            # pull tokens until generator is exhausted
            while True:
                chunk = await loop.run_in_executor(None, safe_next)
                if chunk is None:
                    break

                token = getattr(chunk, "content",
                                getattr(chunk, "text", str(chunk)))
                full_response += token

                # stream out immediately
                await websocket.send_json({"role": "assistant", "chunk": token})

            # persist the completed assistant message
            history[-1][1] = full_response
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

    except WebSocketDisconnect:
        return

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
