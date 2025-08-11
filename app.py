import os
import json
import asyncio
from asyncio import Lock

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from secret_ai_sdk.secret import Secret
from secret_ai_sdk.secret_ai import ChatSecret

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

history_lock = Lock()
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


# Check API key first
@app.get("/api/status")
async def get_api_status():
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        return {"status": "error", "message": "API_KEY environment variable is not set"}

    try:
        # Test connection to SecretAI
        os.environ["SECRET_AI_API_KEY"] = API_KEY
        secret_client = Secret()
        models = secret_client.get_models()
        if not models:
            return {"status": "error", "message": "No models available"}
        return {"status": "ok", "message": "API key is valid"}
    except Exception as e:
        return {"status": "error", "message": f"API connection failed: {str(e)}"}


# Initialize API connection (if available)
llm = None
try:
    API_KEY = os.getenv("API_KEY")
    if API_KEY:
        os.environ["SECRET_AI_API_KEY"] = API_KEY
        secret_client = Secret()
        models = secret_client.get_models()
        if models:
            MODEL = models[0]
            urls = secret_client.get_urls(model=MODEL)
            BASE_URL = urls[0]
            llm = ChatSecret(base_url=BASE_URL, model=MODEL, temperature=1.0)
except Exception as e:
    print(f"Failed to initialize SecretAI client: {e}")


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    # Check if LLM is available
    if llm is None:
        await websocket.send_json({
            "role": "error",
            "message": "SecretAI client not initialized. Please check your API_KEY."
        })
        await websocket.close()
        return

    # load history from data/history.json
    try:
        async with history_lock:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
    except Exception as e:
        await websocket.send_json({
            "role": "error",
            "message": f"Failed to load chat history: {str(e)}"
        })
        await websocket.close()
        return

    try:
        while True:
            user_message = await websocket.receive_text()
            history.append(["user", user_message])
            history.append(["assistant", ""])  # placeholder

            try:
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
                    except Exception as e:
                        raise e

                # pull tokens until generator is exhausted
                while True:
                    try:
                        chunk = await loop.run_in_executor(None, safe_next)
                        if chunk is None:
                            break

                        token = getattr(chunk, "content",
                                        getattr(chunk, "text", str(chunk)))
                        full_response += token

                        # stream out immediately
                        await websocket.send_json({"role": "assistant", "chunk": token})
                    except Exception as e:
                        await websocket.send_json({
                            "role": "error",
                            "message": f"Error during streaming: {str(e)}"
                        })
                        # Remove the incomplete assistant message
                        if history and history[-1][0] == "assistant":
                            history.pop()
                        break

                # persist the completed assistant message (only if successful)
                if full_response:
                    history[-1][1] = full_response
                    try:
                        async with history_lock:
                            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                                json.dump(history, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        await websocket.send_json({
                            "role": "error",
                            "message": f"Failed to save chat history: {str(e)}"
                        })
                await websocket.send_json({
                   "role": "assistant",
                   "done": True
                })

            except Exception as e:
                await websocket.send_json({
                    "role": "error",
                    "message": f"Request failed: {str(e)}"
                })
                # Remove the incomplete messages
                if history and history[-1][0] == "assistant":
                    history.pop()
                if history and history[-1][0] == "user":
                    history.pop()

    except WebSocketDisconnect:
        return
    except Exception as e:
        print(f"WebSocket error: {e}")
        return


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)