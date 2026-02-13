import requests
import json
import datetime
import asyncio
from playwright.async_api import async_playwright

# Ваш системный промпт
SYSTEM_PROMPT = """
You are a Senior Fullstack Developer (PHP/Python) and an expert in OpenEMIS Core. 
Your task is to generate robust automation code.
- Environment: macOS (Monterey), Python 3.13, Playwright 1.48.
- Strict Requirement: Use system Chrome (channel="chrome") to bypass legacy OS library compatibility issues.
- Context: Reference api-docs-v5.json and CakePHP model structures for precision. Use async_playwright exclusively.
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
    url = "http://localhost:8080/v1/chat/completions"
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