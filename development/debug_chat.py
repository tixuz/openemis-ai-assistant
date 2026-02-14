import requests
import json


def ask_ai(prompt):
    """Отправляет вопрос AI и получает ответ"""
    url = "http://localhost:8088/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text}\n")

        data = response.json()
        print(f"JSON структура: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

        # Пробуем разные варианты извлечения ответа
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        elif 'content' in data:
            return data['content']
        elif 'response' in data:
            return data['response']
        else:
            return f"Не могу найти ответ. Полный ответ: {data}"

    except Exception as e:
        print(f"Ошибка: {e}")
        return None


# Тест
print("--- Тест подключения к AI ---")
result = ask_ai("привет")
if result:
    print(f"\nAI ответил: {result}")