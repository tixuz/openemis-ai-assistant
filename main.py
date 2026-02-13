from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import datetime

app = FastAPI()

# Убедимся, что CORS максимально открыт
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # Changed to False to align with the manual OPTIONS handler
    allow_methods=["*"],
    allow_headers=["*"],
)

# Эхо при запуске, чтобы проверить версию
print(f"--- SERVER STARTING AT {datetime.datetime.now()} ---")
print("VERSION: 1.0.6 (CORS DEBUG MODE)")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"\n--- NEW REQUEST ---")
    print(f"METHOD: {request.method}")

    # 1. ПЕРЕХВАТ OPTIONS ДО CALL_NEXT
    if request.method == "OPTIONS":
        print("DEBUG: Catching PNA Preflight inside Middleware")
        return JSONResponse(
            content="OK",
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, x-requested-with",
                "Access-Control-Allow-Private-Network": "true",  # Ключ к успеху
                "Access-Control-Max-Age": "86400",
            }
        )

    # 2. ОСТАЛЬНЫЕ ЗАПРОСЫ (POST и т.д.)
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"ERROR: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request):
    print(f"DEBUG: Handling Private Network Preflight for {request.url}")
    return JSONResponse(
        content="OK",
        headers={
            "Access-Control-Allow-Origin": "https://demo.openemis.org", # Лучше указать явно
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Private-Network": "true", # ВОТ ЭТА СТРОКА РЕШИТ ВСЁ
        }
    )

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        print(f"PAYLOAD RECEIVED: {data}") # Увидим тело сообщения в терминале PyCharm
        user_message = data.get("message", "No message provided")
        return JSONResponse(content={"response": f"Echo from server: {user_message}"})
    except Exception as e:
        print(f"ERROR: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)