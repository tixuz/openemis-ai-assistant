import requests


def ask_ai(prompt):
    """Отправляет вопрос AI и получает ответ"""
    url = "http://localhost:8088/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 256,  # Меньше токенов = быстрее
        "stop": ["<|im_end|>", "\n\n"]  # Останавливаем на этих токенах
    }

    try:
        print("⏳ ", end="", flush=True)
        response = requests.post(url, json=payload, timeout=30)
        print("\r", end="", flush=True)

        data = response.json()

        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content']
            # Очищаем от мусора
            content = content.split('<|im_end|>')[0].strip()
            content = content.split('```')[0].strip()
            return content
        else:
            return "Нет ответа"

    except Exception as e:
        return f"❌ {e}"


print("--- DeepSeek Coder Chat ---")
print("Скорость: ~18 токенов/сек на CPU\n")

while True:
    q = input("Вы: ")
    if q.lower() in ['exit', 'q']: break
    print(f"AI: {ask_ai(q)}\n")