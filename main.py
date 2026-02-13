import os  # Добавили для создания директорий
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import datetime
import requests  # Добавили для связи с DeepSeek
import asyncio
from playwright.async_api import async_playwright
import json

app = FastAPI()

# Константы для связи с локальным ИИ
LLM_SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
# Ваш трехязычный промпт из prompts.md
SYSTEM_PROMPT = """
You are a Senior Fullstack Developer (PHP/Python) and an expert in OpenEMIS Core. 
Your task is to generate robust automation code.
- Environment: macOS (Monterey), Python 3.13, Playwright 1.48.
- Strict Requirement: Use system Chrome (channel="chrome") to bypass legacy OS library compatibility issues.
- Context: Reference api-docs-v5.json and CakePHP model structures for precision. Use async_playwright exclusively.
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"--- SERVER STARTING AT {datetime.datetime.now()} ---")
print("VERSION: 1.0.7 (DeepSeek Integration)")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method == "OPTIONS":
        return JSONResponse(
            content="OK",
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, x-requested-with",
                "Access-Control-Allow-Private-Network": "true",
                "Access-Control-Max-Age": "86400",
            }
        )
    return await call_next(request)


# Добавьте эту функцию в main.py
async def execute_automation(script_code: str):
    async with async_playwright() as p:
        # Используем ваш рабочий метод через системный Chrome
        browser = await p.chromium.launch(headless=False, channel="chrome")
        page = await browser.new_page()
        try:
            # Здесь мы выполняем код, который сгенерировал DeepSeek
            # Для безопасности в реальных проектах используют песочницы,
            # но для локального демо мы доверяем нашему DeepSeek
            exec_scope = {"page": page, "expect": None}
            # Очищаем код от markdown-оберток ```python ... ```
            clean_code = script_code.replace("```python", "").replace("```", "").strip()

            # Выполняем скрипт
            exec(f"async def run():\n{chr(10).join(['    ' + l for l in clean_code.splitlines()])}\n", exec_scope)
            await exec_scope["run"]()

            await page.screenshot(path=f"openemis_result_{datetime.datetime.now().strftime('%H%M%S')}.png")
        finally:
            await browser.close()


# Refactored log_interaction function
def log_interaction(request: Request, user_message: str, ai_response: str, executed_automation: bool = False):
    client_ip = request.client.host
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    log_dir = os.path.join("logs", client_ip, current_date)
    os.makedirs(log_dir, exist_ok=True)
    
    log_file_path = os.path.join(log_dir, "agent_history.jsonl")
    
    log_data = {
        "timestamp": str(datetime.datetime.now()),
        "user_request": user_message,
        "ai_response": ai_response,
        "executed_automation": executed_automation,
        "ip_address": client_ip
    }
    
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")


@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request):
    # Manual OPTIONS handler to ensure preflight requests always get a 200 OK
    print(f"DEBUG: OPTIONS preflight request to {request.url}")
    return JSONResponse(
        content="OK",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400" # Cache preflight for 24 hours
        }
    )

# Обновите эндпоинт, чтобы он вызывал выполнение, если в запросе есть слово "execute"
@app.post("/chat")
async def chat_endpoint(request: Request):
    user_message = "" # Initialize user_message for error logging
    try:
        data = await request.json()
        user_message = data.get("message", "")

        # Запрос к DeepSeek
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        }
        response = requests.post(LLM_SERVER_URL, json=payload)
        ai_response = response.json()['choices'][0]['message']['content']

        automation_triggered = False
        # Если вы попросили "выполни" или "execute", запускаем Playwright
        if "выполни" in user_message.lower() or "run" in user_message.lower():
            asyncio.create_task(execute_automation(ai_response))
            automation_triggered = True
            log_interaction(request, user_message, ai_response, executed_automation=True) # Log when automation is triggered
            return JSONResponse(content={"response": "Код сгенерирован и запущен на выполнение! Проверь окно браузера."})

        log_interaction(request, user_message, ai_response, executed_automation=False) # Log normal AI response
        return JSONResponse(content={"response": ai_response})

    except Exception as e:
        print(f"ERROR: {e}")
        # Log error interactions
        log_interaction(request, user_message, f"ERROR: {str(e)}", executed_automation=False)
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)