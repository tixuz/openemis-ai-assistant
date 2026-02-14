# test_code_analyzer_standalone.py

import os
import re
from pathlib import Path
from typing import List, Dict


class CodeAnalyzer:
    """Analyzes OpenEMIS source code to extract selectors."""

    def __init__(self, openemis_path: str):
        self.openemis_path = Path(openemis_path)
        print(f"\n🔧 Initializing CodeAnalyzer")
        print(f"   Path: {self.openemis_path}")
        print(f"   Exists: {self.openemis_path.exists()}")

        if self.openemis_path.exists():
            # List what's inside
            contents = list(self.openemis_path.iterdir())[:10]
            print(f"   Contents (first 10): {[p.name for p in contents]}")

    def find_selectors_for_task(self, task: str) -> Dict[str, List[str]]:
        """Find relevant selectors based on task keywords."""
        print(f"\n🔍 FINDING SELECTORS FOR: '{task}'")
        print("-" * 70)

        keywords = self._extract_keywords(task)
        print(f"✓ Extracted keywords: {keywords}\n")

        template_files = self._find_template_files(keywords)
        print(f"\n✓ Found {len(template_files)} template files total\n")

        selectors = self._extract_selectors(template_files)

        print(f"\n📊 SUMMARY:")
        print(f"   IDs: {len(selectors['ids'])} unique")
        print(f"   Classes: {len(selectors['classes'])} unique")
        print(f"   Names: {len(selectors['names'])} unique")
        print(f"   Types: {len(selectors['types'])} unique")

        return selectors

    def _extract_keywords(self, task: str) -> List[str]:
        """Extract relevant keywords from task."""
        task_lower = task.lower()

        keyword_map = {
            "login": ["login", "auth", "signin", "user"],
            "student": ["student", "students"],
            "attendance": ["attendance", "absent", "present"],
            "institution": ["institution", "school", "institutions"],
            "staff": ["staff", "teacher", "employee"],
            "grade": ["grade", "mark", "assessment"],
        }

        keywords = []
        for key, values in keyword_map.items():
            if key in task_lower:
                print(f"   Matched '{key}' → Adding: {values}")
                keywords.extend(values)

        if not keywords:
            print(f"   No matches, using default: ['index']")
            keywords = ["index"]

        return keywords

    def _find_template_files(self, keywords: List[str]) -> List[Path]:
        """Find template files matching keywords."""
        print(f"\n📂 SEARCHING FOR TEMPLATE FILES:")
        template_files = []

        # Check if plugins directory exists
        plugins_dir = self.openemis_path / "plugins"
        if not plugins_dir.exists():
            print(f"   ❌ Plugins directory not found: {plugins_dir}")
            return []

        print(f"   ✓ Plugins directory exists: {plugins_dir}")

        # List all plugins
        plugins = list(plugins_dir.iterdir())
        print(f"   Found {len(plugins)} plugins: {[p.name for p in plugins[:5]]}...")

        # Search new-style templates (CakePHP 4+)
        print(f"\n   Searching in plugins/*/templates/...")
        template_dirs = list(self.openemis_path.glob("plugins/*/templates"))
        print(f"   Found {len(template_dirs)} template directories:")
        for td in template_dirs:
            print(f"      - {td.relative_to(self.openemis_path)}")

        for template_dir in template_dirs:
            print(f"\n   Searching in: {template_dir.name}/templates")
            for keyword in keywords:
                pattern = f"*{keyword}*.php"
                print(f"      Pattern: {pattern}")
                matches = list(template_dir.rglob(pattern))
                if matches:
                    print(f"      ✓ Found {len(matches)} files:")
                    for match in matches[:3]:
                        print(f"         • {match.relative_to(self.openemis_path)}")
                    if len(matches) > 3:
                        print(f"         ... and {len(matches) - 3} more")
                else:
                    print(f"      ✗ No matches")
                template_files.extend(matches)

        # Search old-style View templates
        print(f"\n   Searching in plugins/*/View/...")
        view_dirs = list(self.openemis_path.glob("plugins/*/View"))
        print(f"   Found {len(view_dirs)} View directories")

        for view_dir in view_dirs:
            for keyword in keywords:
                pattern = f"*{keyword}*.ctp"
                matches = list(view_dir.rglob(pattern))
                if matches:
                    print(f"      ✓ Found {len(matches)} .ctp files in {view_dir.name}")
                template_files.extend(matches)

        # Deduplicate
        template_files = list(set(template_files))

        # Sort by relevance
        def relevance_score(file: Path) -> int:
            score = 0
            filename_lower = file.name.lower()
            for keyword in keywords:
                if keyword in filename_lower:
                    score += 10
                if keyword == filename_lower.replace('.php', '').replace('.ctp', ''):
                    score += 50
            return score

        template_files.sort(key=relevance_score, reverse=True)

        return template_files[:5]

    def _extract_selectors(self, files: List[Path]) -> Dict[str, any]:
        """Extract HTML selectors from template files."""
        print(f"\n📄 EXTRACTING SELECTORS FROM FILES:")

        selectors = {
            "ids": [],
            "classes": [],
            "names": [],
            "types": [],
            "file_contexts": []
        }

        if not files:
            print("   ⚠️  No files to process!")
            return selectors

        for i, file in enumerate(files, 1):
            try:
                rel_path = file.relative_to(self.openemis_path)
                print(f"\n   [{i}/{len(files)}] Processing: {rel_path}")

                # Check file size
                file_size = file.stat().st_size
                print(f"       Size: {file_size:,} bytes")

                content = file.read_text(encoding='utf-8', errors='ignore')
                print(f"       Content length: {len(content):,} characters")

                # Extract IDs
                ids = re.findall(r'id=["\']([^"\']+)["\']', content)
                print(f"       IDs found: {len(ids)}")
                if ids:
                    print(f"          Examples: {ids[:5]}")
                selectors["ids"].extend([f"#{id}" for id in ids])

                # Extract classes
                classes = re.findall(r'class=["\']([^"\']+)["\']', content)
                print(f"       Class attributes found: {len(classes)}")
                class_count = 0
                for class_str in classes:
                    for cls in class_str.split():
                        if cls and not cls.startswith('<?'):
                            selectors["classes"].append(f".{cls}")
                            class_count += 1
                if classes:
                    print(f"          Individual classes: {class_count}")
                    print(f"          Examples: {list(classes[0].split())[:5] if classes else []}")

                # Extract names
                names = re.findall(r'name=["\']([^"\']+)["\']', content)
                print(f"       Name attributes found: {len(names)}")
                if names:
                    print(f"          Examples: {names[:5]}")
                selectors["names"].extend([f"[name='{name}']" for name in names])

                # Extract types
                types = re.findall(r'type=["\']([^"\']+)["\']', content)
                print(f"       Type attributes found: {len(types)}")
                if types:
                    unique_types = list(set(types))
                    print(f"          Unique types: {unique_types}")
                selectors["types"].extend([f"[type='{t}']" for t in types])

                selectors["file_contexts"].append({
                    "file": str(rel_path),
                    "selectors_count": len(ids) + len(names)
                })

                print(f"       ✓ Total selectors from this file: {len(ids) + len(names) + len(types)}")

            except Exception as e:
                print(f"       ✗ Error reading file: {e}")
                continue

        # Deduplicate
        print(f"\n   🔄 Deduplicating selectors...")
        before_ids = len(selectors["ids"])
        before_classes = len(selectors["classes"])
        before_names = len(selectors["names"])
        before_types = len(selectors["types"])

        selectors["ids"] = list(set(selectors["ids"]))
        selectors["classes"] = list(set(selectors["classes"]))
        selectors["names"] = list(set(selectors["names"]))
        selectors["types"] = list(set(selectors["types"]))

        print(f"      IDs: {before_ids} → {len(selectors['ids'])} unique")
        print(f"      Classes: {before_classes} → {len(selectors['classes'])} unique")
        print(f"      Names: {before_names} → {len(selectors['names'])} unique")
        print(f"      Types: {before_types} → {len(selectors['types'])} unique")

        return selectors

    def format_for_prompt(self, selectors: Dict) -> str:
        """Format selectors for LLM prompt."""
        if not any(selectors.values()):
            return "⚠️ No selectors found"

        lines = ["\n📋 FORMATTED OUTPUT FOR LLM:"]
        lines.append("=" * 70)
        lines.append("AVAILABLE SELECTORS FROM OPENEMIS SOURCE CODE:")

        if selectors.get("ids"):
            lines.append(f"\nIDs ({len(selectors['ids'])} total, showing first 15):")
            lines.append(f"   {', '.join(selectors['ids'][:15])}")

        if selectors.get("names"):
            lines.append(f"\nName attributes ({len(selectors['names'])} total, showing first 15):")
            lines.append(f"   {', '.join(selectors['names'][:15])}")

        if selectors.get("types"):
            unique_types = list(set(selectors['types']))
            lines.append(f"\nType attributes ({len(unique_types)} unique):")
            lines.append(f"   {', '.join(unique_types[:10])}")

        if selectors.get("classes"):
            # Filter useful classes
            useful_classes = [c for c in selectors["classes"]
                              if any(key in c.lower() for key in
                                     ['btn', 'form', 'input', 'submit', 'select'])]
            if useful_classes:
                lines.append(f"\nUseful classes ({len(useful_classes)} total, showing first 15):")
                lines.append(f"   {', '.join(useful_classes[:15])}")

        if selectors.get("file_contexts"):
            lines.append(f"\nFound in files:")
            for ctx in selectors['file_contexts'][:5]:
                lines.append(f"   • {ctx['file']} ({ctx['selectors_count']} selectors)")

        lines.append("=" * 70)
        return "\n".join(lines)


# ===== MAIN TEST =====
if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("  CODE ANALYZER - VERBOSE MODE")
    print("=" * 70)

    # Get OpenEMIS path
    if len(sys.argv) > 1:
        openemis_path = sys.argv[1]
        print(f"Using path from argument: {openemis_path}")
    else:
        # Try common locations
        possible_paths = [
            os.path.expanduser("~/ai_tools/openemis-core"),
            "/openemis-core",
            os.getenv("OPENEMIS_PATH", ""),
            os.getenv("OPENEMIS_SOURCE_PATH", ""),
        ]

        print("\n🔍 Searching for OpenEMIS in common locations:")
        for path in possible_paths:
            if path:
                exists = os.path.exists(path)
                print(f"   {'✓' if exists else '✗'} {path}")
                if exists and not openemis_path:
                    openemis_path = path

        if not openemis_path:
            print("\n❌ OpenEMIS source not found!")
            print("\nUsage: python test_code_analyzer_standalone.py /path/to/openemis-core")
            sys.exit(1)

    print(f"\n✓ Using OpenEMIS at: {openemis_path}")

    # Initialize
    analyzer = CodeAnalyzer(openemis_path)

    # Test cases
    test_cases = [
        "login to openemis",
        "search student",
        "go to institution",
    ]

    for i, task in enumerate(test_cases, 1):
        print("\n\n")
        print("=" * 70)
        print(f"  TEST {i}/{len(test_cases)}: {task.upper()}")
        print("=" * 70)

        selectors = analyzer.find_selectors_for_task(task)
        print(analyzer.format_for_prompt(selectors))

        input("\nPress Enter to continue to next test...")

    print("\n\n✅ All tests complete!")