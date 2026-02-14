# generate_automation_templates.py

import json
from pathlib import Path

# Загружаем базу селекторов
with open("data/selector_database.json") as f:
    db = json.load(f)

print("=" * 70)
print("  GENERATING AUTOMATION TEMPLATES")
print("=" * 70)

templates = []

# Шаблон 1: Логин
if "login to openemis" in db["scenarios"]:
    login_data = db["scenarios"]["login to openemis"]

    template = {
        "id": "tmpl-001",
        "name": "Login to OpenEMIS",
        "description": "Standard login workflow",
        "trigger_phrases": [
            "login",
            "log in to openemis",
            "sign in",
            "authenticate"
        ],
        "commands": [
            {
                "type": "navigate",
                "url": "https://demo.openemis.org/core",
                "description": "Navigate to OpenEMIS login page"
            },
            {
                "type": "fill",
                "selector": login_data["ids"][0] if login_data["ids"] else "[name='username']",
                "value": "{username}",
                "description": "Enter username"
            },
            {
                "type": "fill",
                "selector": login_data["ids"][1] if len(login_data["ids"]) > 1 else "[name='password']",
                "value": "{password}",
                "description": "Enter password"
            },
            {
                "type": "click",
                "selector": "[type='submit']",
                "description": "Click login button"
            },
            {
                "type": "wait_for_navigation",
                "description": "Wait for dashboard to load"
            }
        ],
        "required_variables": ["username", "password"],
        "expected_outcome": "User is logged in and sees dashboard",
        "source_files": login_data["files"]
    }

    templates.append(template)

# Шаблон 2: Поиск студента
if "search student" in db["scenarios"]:
    student_data = db["scenarios"]["search student"]

    template = {
        "id": "tmpl-002",
        "name": "Search Student",
        "description": "Search for a student by name or ID",
        "trigger_phrases": [
            "search student",
            "find student",
            "look up student"
        ],
        "commands": [
            {
                "type": "click",
                "selector": "a[href*='students']",
                "description": "Navigate to students section"
            },
            {
                "type": "fill",
                "selector": "input[type='search']",
                "value": "{student_name}",
                "description": "Enter student name"
            },
            {
                "type": "press_key",
                "key": "Enter",
                "description": "Submit search"
            },
            {
                "type": "wait_for",
                "selector": ".student-results",
                "description": "Wait for results"
            }
        ],
        "required_variables": ["student_name"],
        "expected_outcome": "Student search results displayed",
        "source_files": student_data["files"]
    }

    templates.append(template)

# Шаблон 3: Отметить посещаемость
if "mark attendance" in db["scenarios"]:
    attendance_data = db["scenarios"]["mark attendance"]

    template = {
        "id": "tmpl-003",
        "name": "Mark Student Attendance",
        "description": "Mark students as present or absent",
        "trigger_phrases": [
            "mark attendance",
            "take attendance",
            "attendance for students"
        ],
        "commands": [
            {
                "type": "click",
                "selector": "a[href*='attendance']",
                "description": "Navigate to attendance"
            },
            {
                "type": "fill",
                "selector": "#attendance-date",
                "value": "{date}",
                "description": "Select date"
            },
            {
                "type": "fill",
                "selector": "#student-names",
                "value": "{student_names}",
                "description": "Enter student names"
            },
            {
                "type": "click",
                "selector": "input[value='{status}']",
                "description": "Select absent/present"
            },
            {
                "type": "click",
                "selector": "button[type='submit']",
                "description": "Save attendance"
            }
        ],
        "required_variables": ["date", "student_names", "status"],
        "expected_outcome": "Attendance marked successfully",
        "source_files": attendance_data["files"]
    }

    templates.append(template)

# Сохраняем шаблоны
output_file = Path("data/automation_templates.json")
with open(output_file, 'w') as f:
    json.dump({
        "version": "1.0",
        "generated_from": "selector_database.json",
        "total_templates": len(templates),
        "templates": templates
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Generated {len(templates)} templates")
print(f"   Saved to: {output_file}")

# Вывод примера
print("\n📋 Example Template:")
print(json.dumps(templates[0], indent=2, ensure_ascii=False))