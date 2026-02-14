# view_database.py

import json
from pathlib import Path

db_file = Path("data/selector_database.json")

if not db_file.exists():
    print("❌ Database not found. Run build_selector_database.py first!")
    exit(1)

with open(db_file) as f:
    db = json.load(f)

print("=" * 70)
print("  SELECTOR DATABASE")
print("=" * 70)
print(f"Generated: {db['generated_at']}")
print(f"Total scenarios: {db['total_scenarios']}")
print()

# Показать топ-10 сценариев с наибольшим количеством селекторов
scenarios_sorted = sorted(
    db['scenarios'].items(),
    key=lambda x: x[1]['total_selectors'],
    reverse=True
)

print("📊 Top 10 scenarios by selector count:")
print()

for i, (name, data) in enumerate(scenarios_sorted[:10], 1):
    print(f"{i}. {name}")
    print(f"   Selectors: {data['total_selectors']}")
    print(f"   IDs: {len(data['ids'])}, Names: {len(data['names'])}, Classes: {len(data['classes'])}")
    print(f"   Files: {len(data['files'])}")
    print()