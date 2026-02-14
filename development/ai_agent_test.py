import requests
import asyncio
from playwright.async_api import async_playwright


# 1. Спрашиваем у нашего DeepSeek
def ask_deepseek(prompt):
    url = "http://localhost:8080/v1/chat/completions"
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "deepseek-v2-lite"
    }
    response = requests.post(url, json=data)
    return response.json()['choices'][0]['message']['content']


# 2. Выполняем действие в браузере
async def run_playwright():
    print("DeepSeek говорит:", ask_deepseek("Write a short greeting for an OpenEMIS developer"))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        page = await browser.new_page()
        await page.goto("https://demo.openemis.org")
        print(f"Зашли на сайт! Заголовок: {await page.title()}")
        await page.screenshot(path="openemis_success.png")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_playwright())