# test_analyzer.py
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.core.code_analyzer import get_code_analyzer

# Initialize analyzer
analyzer = get_code_analyzer("~/ai_tools/openemis-core")

# Test 1: Login
print("=" * 60)
print("Test 1: Login")
print("=" * 60)
selectors = analyzer.find_selectors_for_task("login to openemis")
print(analyzer.format_for_prompt(selectors))
print()

# Test 2: Student
print("=" * 60)
print("Test 2: Students")
print("=" * 60)
selectors = analyzer.find_selectors_for_task("search student")
print(analyzer.format_for_prompt(selectors))
print()

# Test 3: Institution
print("=" * 60)
print("Test 3: Institution")
print("=" * 60)
selectors = analyzer.find_selectors_for_task("go to institution")
print(analyzer.format_for_prompt(selectors))