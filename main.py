import os
import re
import json
import asyncio
import datetime
import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright

app = FastAPI()

# Configuration
LLM_SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
SYSTEM_PROMPT = """
You are a Senior Fullstack Developer (PHP/Python) and an expert in OpenEMIS Core. 
Task: Generate robust automation code.
- Env: macOS (Monterey), Python 3.13, Playwright 1.48.
- Requirements: Use channel="chrome", async_playwright exclusively.
- Precision: Reference api-docs-v5.json and CakePHP model structures.
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def execute_automation(script_code: str):
    """Parses and runs the generated Playwright code"""
    async with async_playwright() as p:
        # Launch system Chrome to bypass legacy OS issues
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        try:
            # Extract code between triple backticks
            match = re.search(r"```python\n(.*?)\n```", script_code, re.DOTALL)
            code_to_run = match.group(1) if match else script_code.replace("```", "")

            exec_scope = {"page": page, "asyncio": asyncio}
            formatted_code = f"async def run_task():\n" + "\n".join(f"    {line}" for line in code_to_run.splitlines())

            exec(formatted_code, exec_scope)
            await exec_scope["run_task"]()

            # Save result with timestamp
            ts = datetime.datetime.now().strftime("%H%M%S")
            await page.screenshot(path=f"logs/screenshot_{ts}.png")
        except Exception as e:
            print(f"Automation Execution Error: {e}")
        finally:
            await browser.close()


def log_interaction(request: Request, user_message: str, ai_response: str, executed: bool):
    """Thread-safe logging to partitioned directory"""
    client_ip = request.client.host
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join("logs", client_ip, date_str)
    os.makedirs(log_dir, exist_ok=True)

    log_entry = {
        "timestamp": str(datetime.datetime.now()),
        "request": user_message,
        "ai_output": ai_response,
        "executed": executed,
        "ip": client_ip
    }
    with open(os.path.join(log_dir, "history.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        msg = data.get("message", "").lower()

        # Request to local DeepSeek
        payload = {"messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": msg}]}
        ai_raw = requests.post(LLM_SERVER_URL, json=payload, timeout=60).json()
        ai_text = ai_raw['choices'][0]['message']['content']

        is_action = any(word in msg for word in ["выполни", "run", "execute", "click"])

        if is_action:
            asyncio.create_task(execute_automation(ai_text))
            log_interaction(request, msg, ai_text, True)
            return JSONResponse({"response": "Код сгенерирован и запущен. Проверьте Chrome."})

        log_interaction(request, msg, ai_text, False)
        return JSONResponse({"response": ai_text})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    print(f"--- AGENT SERVER READY | {datetime.datetime.now()} ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)