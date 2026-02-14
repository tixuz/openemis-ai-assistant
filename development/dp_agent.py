import requests
import json
import datetime
import asyncio
from playwright.async_api import async_playwright

# Ваш системный промпт
# ✅ GOOD - Specific, constrained, with examples
SYSTEM_PROMPT = """You are a Playwright automation code generator for OpenEMIS Core.

CRITICAL RULES:
1. Output ONLY valid JSON - no explanations, no markdown, no preamble
2. Use ONLY these 10 commands: navigate, click, fill, wait_for, wait_for_navigation, screenshot, extract_text, handle_dialog, select_option, press_key
3. All URLs must start with https://demo.openemis.org
4. Return array of command objects

OUTPUT FORMAT (MANDATORY):
{
  "commands": [
    {"type": "navigate", "url": "https://demo.openemis.org/..."},
    {"type": "click", "selector": "css-selector-here"},
    {"type": "fill", "selector": "#input", "value": "text"}
  ]
}

EXAMPLES:

USER: "Login to OpenEMIS as admin"
ASSISTANT: {
  "commands": [
    {"type": "navigate", "url": "https://demo.openemis.org/core"},
    {"type": "fill", "selector": "#username", "value": "admin"},
    {"type": "fill", "selector": "#password", "value": "demo"},
    {"type": "click", "selector": "button[type='submit']"},
    {"type": "wait_for_navigation"}
  ]
}

USER: "Go to students page"
ASSISTANT: {
  "commands": [
    {"type": "click", "selector": "a[href*='students']"},
    {"type": "wait_for", "selector": ".students-table"}
  ]
}

USER: "Search for institution P1002"
ASSISTANT: {
  "commands": [
    {"type": "click", "selector": "#institutions-menu"},
    {"type": "fill", "selector": "input[name='search']", "value": "P1002"},
    {"type": "press_key", "key": "Enter"},
    {"type": "wait_for", "selector": ".institution-card"}
  ]
}

Now generate commands for the user's request. Remember: ONLY JSON output, no other text.
"""


def log_to_file(data):
    """Добавляет запись в ваш файл истории"""
    with open("agent_history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


async def execute_code(script_code):
    """Метод для исполнения сгенерированного кода"""
    async with async_playwright() as p:
        # Принудительно используем системный Chrome для вашей macOS
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        # Очистка и выполнение кода
        clean_code = script_code.replace("```python", "").replace("```", "").strip()
        # Создаем пространство имен для exec
        scope = {"page": page, "asyncio": asyncio}
        try:
            # Превращаем текст в исполняемую функцию
            exec(f"async def run_task():\n{chr(10).join(['    ' + l for l in clean_code.splitlines()])}", scope)
            await scope["run_task"]()
            return True
        except Exception as e:
            print(f"Ошибка выполнения: {e}")
            return False
        finally:
            await browser.close()


def ask_ai(prompt):
    url = "http://localhost:8088/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    r = requests.post(url, json=payload)
    return r.json()['choices'][0]['message']['content']


async def main_loop():
    print("--- DEEPSEEK AGENT CLI READY ---")
    while True:
        cmd = input(">>> ")
        if cmd.lower() in ['exit', 'quit']: break

        ai_response = ask_ai(cmd)
        print(f"\nAI предложил код:\n{ai_response}\n")

        # Решаем, запускать ли автоматизацию
        executed = False
        if "run" in cmd.lower() or "выполни" in cmd.lower():
            print("Запускаю Playwright...")
            executed = await execute_code(ai_response)

        # Логируем результат
        log_to_file({
            "timestamp": str(datetime.datetime.now()),
            "user_request": cmd,
            "ai_response": ai_response,
            "executed_automation": executed
        })


if __name__ == "__main__":
    asyncio.run(main_loop())