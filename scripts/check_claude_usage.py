#!/usr/bin/env python3
"""
Check Claude API Usage - найди где утекают деньги!

Usage:
    python check_claude_usage.py
"""

import os
import re
from pathlib import Path


def check_model_usage():
    """Проверяет какую модель используешь в коде"""
    print("🔍 Проверяю какую модель Claude используешь...")
    print("=" * 60)

    project_root = Path.cwd()
    opus_count = 0
    sonnet_count = 0
    haiku_count = 0

    files_with_opus = []
    files_with_sonnet = []

    # Ищем Python файлы
    for py_file in project_root.rglob("*.py"):
        if 'venv' in str(py_file) or '.git' in str(py_file):
            continue

        try:
            content = py_file.read_text()

            if 'opus' in content.lower():
                opus_count += content.lower().count('opus')
                files_with_opus.append(py_file)

            if 'sonnet' in content.lower():
                sonnet_count += content.lower().count('sonnet')
                files_with_sonnet.append(py_file)

            if 'haiku' in content.lower():
                haiku_count += content.lower().count('haiku')

        except Exception:
            pass

    print(f"\n📊 Статистика моделей:")
    print(f"   Opus упоминаний: {opus_count}")
    print(f"   Sonnet упоминаний: {sonnet_count}")
    print(f"   Haiku упоминаний: {haiku_count}")

    if opus_count > 0:
        print(f"\n❌ ПРОБЛЕМА! Используешь Opus в {len(files_with_opus)} файлах:")
        for f in files_with_opus[:5]:
            print(f"   - {f.relative_to(project_root)}")
        print(f"\n💰 Opus стоит 5x ДОРОЖЕ Sonnet!")
        print(f"   Potential savings: ~$72 за 2 дня")
        print(f"\n✅ FIX: Замени 'opus' на 'sonnet' в этих файлах")
    else:
        print(f"\n✅ Хорошо! Не используешь дорогой Opus")

    if sonnet_count > 0:
        print(f"\n✅ Используешь Sonnet (правильно!)")


def check_max_tokens():
    """Проверяет есть ли ограничение max_tokens"""
    print("\n" + "=" * 60)
    print("🔍 Проверяю использование max_tokens...")
    print("=" * 60)

    project_root = Path.cwd()
    files_without_limit = []

    for py_file in project_root.rglob("*.py"):
        if 'venv' in str(py_file) or '.git' in str(py_file):
            continue

        try:
            content = py_file.read_text()

            # Ищем вызовы Claude API
            if 'messages.create' in content or 'anthropic' in content.lower():
                if 'max_tokens' not in content:
                    files_without_limit.append(py_file)

        except Exception:
            pass

    if files_without_limit:
        print(f"\n⚠️  Найдено {len(files_without_limit)} файлов БЕЗ max_tokens:")
        for f in files_without_limit[:5]:
            print(f"   - {f.relative_to(project_root)}")
        print(f"\n💰 Без max_tokens Claude может генерировать 4096 токенов!")
        print(f"   Это может стоить дорого для длинных ответов")
        print(f"\n✅ FIX: Добавь max_tokens=2048 (или меньше)")
    else:
        print(f"\n✅ Хорошо! max_tokens используется")


def check_cursor_config():
    """Проверяет конфиг Cursor/Windsurf"""
    print("\n" + "=" * 60)
    print("🔍 Проверяю Cursor/Windsurf конфигурацию...")
    print("=" * 60)

    # Ищем .cursor или .windsurf директории
    cursor_dir = Path.home() / '.cursor'
    windsurf_dir = Path.home() / '.windsurf'

    if cursor_dir.exists():
        print(f"\n⚠️  Cursor установлен!")
        print(f"   Cursor может делать сотни запросов автоматически")
        print(f"\n💡 РЕКОМЕНДАЦИЯ:")
        print(f"   1. Открой Cursor Settings")
        print(f"   2. Отключи 'Auto-apply suggestions'")
        print(f"   3. Отключи 'Background indexing'")
        print(f"   4. Используй только Manual mode")

    elif windsurf_dir.exists():
        print(f"\n⚠️  Windsurf установлен!")
        print(f"   Аналогично Cursor - много auto-requests")

    else:
        print(f"\n✅ Cursor/Windsurf не найдены")


def estimate_costs():
    """Оценивает стоимость для разных сценариев"""
    print("\n" + "=" * 60)
    print("💰 ОЦЕНКА СТОИМОСТИ")
    print("=" * 60)

    print(f"\n📊 Стоимость за 100 requests:")
    print(f"\nОпус (claude-opus-4):")
    print(f"   Input (500K tokens avg):  $7.50")
    print(f"   Output (100K tokens avg): $7.50")
    print(f"   TOTAL per 100 requests:   $15.00")

    print(f"\nСоннет (claude-sonnet-4):")
    print(f"   Input (500K tokens avg):  $1.50")
    print(f"   Output (100K tokens avg): $1.50")
    print(f"   TOTAL per 100 requests:   $3.00")

    print(f"\n💡 SAVINGS: Sonnet = 5x дешевле!")

    print(f"\n📊 Для твоих $90:")
    print(f"   С Opus:   ~600 requests")
    print(f"   С Sonnet: ~3000 requests")
    print(f"\n   Если ты сделал < 600 requests → используешь Opus!")
    print(f"   Если ты сделал > 600 requests → ОК, но слишком много")


def main():
    print("\n" + "=" * 60)
    print("  🔍 CLAUDE API USAGE CHECKER")
    print("  Найдем где утекают твои $90!")
    print("=" * 60)

    check_model_usage()
    check_max_tokens()
    check_cursor_config()
    estimate_costs()

    print("\n" + "=" * 60)
    print("✅ Проверка завершена!")
    print("=" * 60)
    print(f"\n💡 QUICK WINS:")
    print(f"   1. Замени 'opus' → 'sonnet' (5x дешевле)")
    print(f"   2. Добавь max_tokens=2048")
    print(f"   3. Используй prompt caching")
    print(f"   4. Batch requests когда возможно")
    print(f"\n📈 Expected savings: $90 → $5-10 per project")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
    main()