# analyze_top_scenarios.py

import json
from pathlib import Path

db_file = Path("data/selector_database.json")

with open(db_file) as f:
    db = json.load(f)

# Анализируем топ сценарии
top_scenarios = [
    "login to openemis",
    "mark attendance",
    "search student",
    "go to institution"
]

print("=" * 70)
print("  DETAILED SCENARIO ANALYSIS")
print("=" * 70)

for scenario in top_scenarios:
    if scenario not in db['scenarios']:
        print(f"\n⚠️  '{scenario}' not in database")
        continue

    data = db['scenarios'][scenario]

    print(f"\n{'=' * 70}")
    print(f"📋 {scenario.upper()}")
    print(f"{'=' * 70}")

    print(f"\n📊 Statistics:")
    print(f"   Total selectors: {data['total_selectors']}")
    print(f"   IDs: {len(data['ids'])}")
    print(f"   Names: {len(data['names'])}")
    print(f"   Classes: {len(data['classes'])}")
    print(f"   Navigation: {len(data.get('navigation_items', []))}")

    print(f"\n🆔 IDs (first 10):")
    for id in data['ids'][:10]:
        print(f"   • {id}")

    print(f"\n📝 Name attributes (first 10):")
    for name in data['names'][:10]:
        print(f"   • {name}")

    if data.get('navigation_items'):
        print(f"\n🧭 Navigation items:")
        for nav in data['navigation_items'][:10]:
            print(f"   • {nav}")

    print(f"\n📁 Source files:")
    for file in data['files'][:5]:
        print(f"   • {file}")

    print()
    input("Press Enter for next scenario...")