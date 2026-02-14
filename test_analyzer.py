# test_analyzer.py
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.core.code_analyzer import get_code_analyzer

# ========== НОВОЕ: Удаление кеша ==========
force_refresh = "--force" in sys.argv or "-f" in sys.argv

if force_refresh:
    print("\n🔄 FORCE REFRESH - Clearing cache...")
    import shutil

    cache_dir = Path("data/code_analysis_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    print("   ✓ Cache cleared\n")
# ==========================================

# Initialize analyzer
analyzer = get_code_analyzer("~/ai_tools/openemis-core")

# Test cases
test_cases = [
    "login to openemis",
    "search student",
    "go to institution"
]

for i, task in enumerate(test_cases, 1):
    print("\n" + "=" * 60)
    print(f"Test {i}: {task.title()}")
    print("=" * 60)

    selectors = analyzer.find_selectors_for_task(task, force_refresh=force_refresh)

    # ========== НОВОЕ: Показать статистику ==========
    print(f"\n📊 STATISTICS:")
    print(f"   IDs: {len(selectors.get('ids', []))}")
    print(f"   Names: {len(selectors.get('names', []))}")
    print(f"   Classes: {len(selectors.get('classes', []))}")
    print(f"   Navigation: {len(selectors.get('navigation_items', []))}")
    print(f"   Files: {len(selectors.get('file_contexts', []))}")
    # ================================================

    print(analyzer.format_for_prompt(selectors))
    print()