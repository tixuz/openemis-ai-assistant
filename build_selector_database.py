# build_selector_database.py

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from backend.core.code_analyzer import get_code_analyzer

print("=" * 70)
print("  BUILDING OPENEMIS SELECTOR DATABASE")
print("=" * 70)

analyzer = get_code_analyzer("~/ai_tools/openemis-core")

# Все возможные задачи/сценарии в OpenEMIS
scenarios = [
    # Authentication
    "login to openemis",
    "logout from system",
    "change password",
    "forgot password",

    # Students
    "search student",
    "add new student",
    "edit student information",
    "view student profile",
    "student attendance",
    "student grades",
    "student enrollment",
    "transfer student",

    # Institutions
    "go to institution",
    "search institution",
    "add institution",
    "edit institution",
    "view institution details",

    # Staff
    "add staff member",
    "search staff",
    "view staff profile",
    "staff attendance",

    # Classes
    "create class",
    "assign students to class",
    "view class list",

    # Attendance
    "mark attendance",
    "view attendance report",
    "mark student absent",
    "mark student present",

    # Grades/Assessment
    "enter grades",
    "view grade report",
    "create assessment",

    # Reports
    "generate student report",
    "export attendance report",
    "view statistics",

    # Navigation
    "go to dashboard",
    "open navigation menu",
    "access settings",
]

database = {
    "generated_at": datetime.now().isoformat(),
    "openemis_path": str(analyzer.openemis_path),
    "total_scenarios": len(scenarios),
    "scenarios": {}
}

print(f"\n🔍 Analyzing {len(scenarios)} scenarios...\n")

for i, scenario in enumerate(scenarios, 1):
    print(f"[{i}/{len(scenarios)}] {scenario}")
    print("-" * 70)

    # Сканируем с force_refresh чтобы не использовать старый кеш
    selectors = analyzer.find_selectors_for_task(scenario, force_refresh=True)

    # Сохраняем в базу
    database["scenarios"][scenario] = {
        "ids": selectors.get("ids", []),
        "names": selectors.get("names", []),
        "classes": selectors.get("classes", []),
        "types": selectors.get("types", []),
        "navigation_items": selectors.get("navigation_items", []),
        "files": [ctx["file"] for ctx in selectors.get("file_contexts", [])],
        "total_selectors": (
                len(selectors.get("ids", [])) +
                len(selectors.get("names", [])) +
                len(selectors.get("classes", []))
        )
    }

    print(f"   ✓ Found {database['scenarios'][scenario]['total_selectors']} selectors")
    print()

# Сохраняем базу
output_file = Path("data/selector_database.json")
output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, 'w') as f:
    json.dump(database, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print(f"✅ Database saved to: {output_file}")
print(f"   Total scenarios: {len(scenarios)}")
print(f"   Total unique files analyzed: {len(set(sum([s['files'] for s in database['scenarios'].values()], [])))}")
print("=" * 70)