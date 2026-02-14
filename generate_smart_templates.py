# generate_smart_templates.py

import json
from pathlib import Path

# Load database
with open("data/selector_database.json") as f:
    db = json.load(f)

templates = []

# ============================================================
# TEMPLATE 1: LOGIN
# ============================================================
if "login to openemis" in db["scenarios"]:
    login = db["scenarios"]["login to openemis"]

    # Найдем самые релевантные селекторы
    username_selector = None
    password_selector = None
    submit_selector = None

    # Ищем username
    for id in login['ids']:
        if 'username' in id.lower():
            username_selector = id
            break
    if not username_selector:
        for name in login['names']:
            if 'username' in name.lower():
                username_selector = name
                break

    # Ищем password
    for id in login['ids']:
        if 'password' in id.lower():
            password_selector = id
            break
    if not password_selector:
        for name in login['names']:
            if 'password' in name.lower():
                password_selector = name
                break

    # Ищем submit button
    for name in login['names']:
        if 'submit' in name.lower():
            submit_selector = name
            break
    if not submit_selector:
        submit_selector = "[type='submit']"

    template = {
        "id": "tmpl-001-login",
        "name": "Login to OpenEMIS",
        "intent": "LOGIN",
        "confidence": 0.95,
        "trigger_keywords": ["login", "log in", "sign in", "authenticate"],
        "commands": [
            {
                "step": 1,
                "type": "navigate",
                "url": "https://demo.openemis.org/core",
                "description": "Navigate to OpenEMIS login page"
            },
            {
                "step": 2,
                "type": "fill",
                "selector": username_selector or "[name='username']",
                "value": "{username}",
                "description": "Enter username",
                "fallback_selectors": ["#username", "[name='username']", "input[type='text']"]
            },
            {
                "step": 3,
                "type": "fill",
                "selector": password_selector or "[name='password']",
                "value": "{password}",
                "description": "Enter password",
                "fallback_selectors": ["#password", "[name='password']", "input[type='password']"]
            },
            {
                "step": 4,
                "type": "click",
                "selector": submit_selector,
                "description": "Click login button",
                "fallback_selectors": ["button[type='submit']", ".btn-primary", "#login-btn"]
            },
            {
                "step": 5,
                "type": "wait_for_navigation",
                "description": "Wait for dashboard"
            }
        ],
        "variables": {
            "username": {"type": "string", "required": True, "default": "admin"},
            "password": {"type": "string", "required": True, "default": "demo"}
        },
        "success_indicators": [
            {"type": "url_contains", "value": "/dashboard"},
            {"type": "element_visible", "selector": ".user-menu"}
        ],
        "source_files": login['files']
    }

    templates.append(template)
    print(f"✓ Created template: {template['name']}")
    print(f"   Username selector: {username_selector}")
    print(f"   Password selector: {password_selector}")
    print(f"   Submit selector: {submit_selector}")

# ============================================================
# TEMPLATE 2: MARK ATTENDANCE
# ============================================================
if "mark attendance" in db["scenarios"]:
    attendance = db["scenarios"]["mark attendance"]

    # Ищем релевантные селекторы
    date_selector = None
    student_selector = None
    status_selector = None

    for id in attendance['ids']:
        if 'date' in id.lower() or 'attendance' in id.lower():
            date_selector = id
            break

    for id in attendance['ids']:
        if 'student' in id.lower():
            student_selector = id
            break

    template = {
        "id": "tmpl-002-attendance",
        "name": "Mark Student Attendance",
        "intent": "MARK_ATTENDANCE",
        "confidence": 0.90,
        "trigger_keywords": ["mark attendance", "attendance", "absent", "present", "missing"],
        "commands": [
            {
                "step": 1,
                "type": "click",
                "selector": "a[href*='attendance']",
                "description": "Navigate to attendance",
                "fallback_selectors": [
                    nav for nav in attendance.get('navigation_items', [])
                    if 'attendance' in nav.lower()
                ][:3]
            },
            {
                "step": 2,
                "type": "fill",
                "selector": date_selector or "#attendance-date",
                "value": "{date}",
                "description": "Select date",
                "fallback_selectors": ["[name*='date']", "#date", "input[type='date']"]
            },
            {
                "step": 3,
                "type": "fill",
                "selector": student_selector or "#student-names",
                "value": "{students}",
                "description": "Enter student names",
                "fallback_selectors": ["[name*='student']", "#students"]
            },
            {
                "step": 4,
                "type": "click",
                "selector": "input[value='{status}']",
                "description": "Select absent/present status"
            },
            {
                "step": 5,
                "type": "click",
                "selector": "[type='submit']",
                "description": "Save attendance"
            }
        ],
        "variables": {
            "date": {"type": "date", "required": True, "default": "today"},
            "students": {"type": "array", "required": True},
            "status": {"type": "enum", "values": ["absent", "present"], "default": "absent"}
        },
        "entity_extraction": {
            "students": {"patterns": ["capitalized_words", "after:absent", "after:missing"]},
            "status": {"patterns": ["absent|missing→absent", "present→present"]},
            "date": {"patterns": ["today", "yesterday", "YYYY-MM-DD"]}
        },
        "success_indicators": [
            {"type": "text_contains", "value": "saved successfully"},
            {"type": "element_visible", "selector": ".success-message"}
        ],
        "source_files": attendance['files']
    }

    templates.append(template)
    print(f"✓ Created template: {template['name']}")

# ============================================================
# TEMPLATE 3: SEARCH STUDENT
# ============================================================
if "search student" in db["scenarios"]:
    student = db["scenarios"]["search student"]

    search_selector = None
    for id in student['ids']:
        if 'search' in id.lower():
            search_selector = id
            break

    template = {
        "id": "tmpl-003-search-student",
        "name": "Search Student",
        "intent": "SEARCH_STUDENT",
        "confidence": 0.88,
        "trigger_keywords": ["search student", "find student", "student search"],
        "commands": [
            {
                "step": 1,
                "type": "click",
                "selector": "a[href*='students']",
                "description": "Navigate to students",
                "fallback_selectors": [
                    nav for nav in student.get('navigation_items', [])
                    if 'student' in nav.lower()
                ][:3]
            },
            {
                "step": 2,
                "type": "fill",
                "selector": search_selector or "input[type='search']",
                "value": "{student_name}",
                "description": "Enter student name",
                "fallback_selectors": ["#search", "[name='search']", "input[placeholder*='search']"]
            },
            {
                "step": 3,
                "type": "press_key",
                "key": "Enter",
                "description": "Submit search"
            },
            {
                "step": 4,
                "type": "wait_for",
                "selector": ".student-results, .table, [class*='result']",
                "description": "Wait for results"
            }
        ],
        "variables": {
            "student_name": {"type": "string", "required": True}
        },
        "success_indicators": [
            {"type": "element_visible", "selector": ".student-results"},
            {"type": "text_visible", "value": "result"}
        ],
        "source_files": student['files']
    }

    templates.append(template)
    print(f"✓ Created template: {template['name']}")

# ============================================================
# TEMPLATE 4: GO TO INSTITUTION
# ============================================================
if "go to institution" in db["scenarios"]:
    institution = db["scenarios"]["go to institution"]

    code_selector = None
    for id in institution['ids']:
        if 'code' in id.lower() or 'institution' in id.lower():
            code_selector = id
            break

    template = {
        "id": "tmpl-004-institution",
        "name": "Go to Institution",
        "intent": "SEARCH_INSTITUTION",
        "confidence": 0.87,
        "trigger_keywords": ["institution", "school", "go to institution"],
        "commands": [
            {
                "step": 1,
                "type": "click",
                "selector": "a[href*='institutions']",
                "description": "Navigate to institutions",
                "fallback_selectors": [
                    nav for nav in institution.get('navigation_items', [])
                    if 'institution' in nav.lower()
                ][:3]
            },
            {
                "step": 2,
                "type": "fill",
                "selector": code_selector or "input[name*='code']",
                "value": "{institution_code}",
                "description": "Enter institution code",
                "fallback_selectors": ["#code", "[name='search']", "input[type='search']"]
            },
            {
                "step": 3,
                "type": "press_key",
                "key": "Enter",
                "description": "Search"
            },
            {
                "step": 4,
                "type": "wait_for",
                "selector": ".institution-card, .table",
                "description": "Wait for results"
            }
        ],
        "variables": {
            "institution_code": {"type": "string", "required": True, "pattern": "[A-Z]\\d{4}"}
        },
        "entity_extraction": {
            "institution_code": {"patterns": ["P1002", "P-1002", "[A-Z]\\d{4}"]}
        },
        "success_indicators": [
            {"type": "element_visible", "selector": ".institution-details"}
        ],
        "source_files": institution['files']
    }

    templates.append(template)
    print(f"✓ Created template: {template['name']}")

# ============================================================
# SAVE ALL TEMPLATES
# ============================================================
output = {
    "version": "2.0",
    "generated_from": "selector_database.json",
    "generated_at": db['generated_at'],
    "total_templates": len(templates),
    "templates": {t['id']: t for t in templates}
}

output_file = Path("data/smart_automation_templates.json")
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n{'=' * 70}")
print(f"✅ Generated {len(templates)} smart templates")
print(f"   Saved to: {output_file}")
print(f"{'=' * 70}")

# Show summary
print("\n📋 Templates Summary:")
for t in templates:
    print(f"\n{t['id']}: {t['name']}")
    print(f"   Intent: {t['intent']}")
    print(f"   Steps: {len(t['commands'])}")
    print(f"   Variables: {list(t['variables'].keys())}")
    print(f"   Source files: {len(t['source_files'])}")