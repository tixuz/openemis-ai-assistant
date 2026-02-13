import requests

SYSTEM_PROMPT = """
You are a Senior Fullstack Developer (PHP/Python) and an expert in OpenEMIS Core. 
Your task is to generate robust automation code.
- Environment: macOS (Monterey), Python 3.13, Playwright 1.48.
- Strict Requirement: Use system Chrome (channel="chrome") to bypass legacy OS library compatibility issues.
- Context: Reference api-docs-v5.json and CakePHP model structures for precision. Use async_playwright exclusively.
"""

def ask_ai(prompt):
    # Прямой запрос к вашему запущенному серверу
    url = "http://localhost:8080/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2 # Для кода лучше ставить низкую температуру
    }
    r = requests.post(url, json=payload)
    return r.json()['choices'][0]['message']['content']

if __name__ == "__main__":
    while True:
        cmd = input(">>> ")
        print(ask_ai(cmd))