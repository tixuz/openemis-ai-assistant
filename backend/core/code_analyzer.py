# backend/core/code_analyzer.py
"""
Code Analyzer - Extract Real Selectors from OpenEMIS Source Code

Analyzes OpenEMIS PHP templates, controllers, and components to extract
actual CSS selectors, IDs, names, and navigation items. This ensures
automation scripts use real selectors instead of guessing.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class CodeAnalyzer:
    """Analyzes OpenEMIS source code to extract selectors."""

    def __init__(self, openemis_path: str = "~/ai_tools/openemis-core"):
        # Expand ~ to full path
        expanded_path = os.path.expanduser(openemis_path)
        self.openemis_path = Path(expanded_path)

        # Cache directory
        self.cache_dir = Path("data/code_analysis_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache TTL (time to live)
        self.cache_ttl = timedelta(hours=24)  # Refresh every 24 hours

        print(f"\n🔧 CodeAnalyzer initialized")
        print(f"   OpenEMIS: {self.openemis_path}")
        print(f"   Exists: {self.openemis_path.exists()}")
        print(f"   Cache: {self.cache_dir}")

    def find_selectors_for_task(
        self, 
        task: str, 
        use_llm: bool = False, 
        force_refresh: bool = False
    ) -> Dict[str, List[str]]:
        """
        Find relevant selectors based on task keywords.

        Args:
            task: User task like "login to openemis"
            use_llm: Whether to use LLM for intelligent analysis
            force_refresh: Ignore cache and rescan

        Returns:
            Dictionary with selectors and metadata
        """
        # Generate cache key
        cache_key = self._get_cache_key(task)
        
        # Check cache first (unless force_refresh)
        if not force_refresh:
            cached = self._load_from_cache(cache_key)
            if cached:
                # Check if cache has actual data
                has_data = any(cached.get(k) for k in ["ids", "names", "classes", "navigation_items"])
                if has_data:
                    print(f"✓ Using cached selectors for '{task}'")
                    return cached
                else:
                    print(f"⚠️  Cache exists but empty - rescanning")

        print(f"\n🔍 Analyzing code for: '{task}'")

        # Extract keywords
        keywords = self._extract_keywords(task)
        print(f"   Keywords: {keywords}")

        # Find files in ALL locations
        all_files = self._find_all_files(keywords)
        print(f"   Found {len(all_files)} files total")

        # Extract selectors
        selectors = self._extract_selectors(all_files)

        # Save to cache
        self._save_to_cache(cache_key, selectors)

        return selectors

    def _get_cache_key(self, task: str) -> str:
        """Generate cache key from task."""
        return hashlib.md5(task.encode()).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load selectors from cache if not expired."""
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check if expired
        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_age > self.cache_ttl:
            print(f"   Cache expired (age: {file_age})")
            return None

        with open(cache_file, 'r') as f:
            return json.load(f)

    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save selectors to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Add metadata
        data['_cached_at'] = datetime.now().isoformat()

        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"   💾 Saved to cache: {cache_file.name}")

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
            "navigation": ["navigation", "menu", "nav"],
        }

        keywords = []
        for key, values in keyword_map.items():
            if key in task_lower:
                keywords.extend(values)

        return keywords if keywords else ["index"]

    def _find_all_files(self, keywords: List[str]) -> List[Path]:
        """Find files in ALL OpenEMIS locations."""
        if not self.openemis_path.exists():
            print(f"      ❌ OpenEMIS path doesn't exist: {self.openemis_path}")
            return []

        all_files = []

        # 1. Templates (Views)
        print(f"\n   📂 Searching templates...")
        template_dirs = list(self.openemis_path.glob("plugins/*/templates"))
        for template_dir in template_dirs:
            for keyword in keywords:
                matches = list(template_dir.rglob(f"*{keyword}*.php"))
                if matches:
                    print(f"      ✓ {len(matches)} in {template_dir.name}/templates")
                all_files.extend(matches)

        # 2. Controllers
        print(f"\n   📂 Searching controllers...")
        controller_dir = self.openemis_path / "src" / "Controller"
        if controller_dir.exists():
            for keyword in keywords:
                matches = list(controller_dir.rglob(f"*{keyword}*.php"))
                if matches:
                    print(f"      ✓ {len(matches)} controllers")
                all_files.extend(matches)

        # 3. Components (IMPORTANT for navigation!)
        print(f"\n   📂 Searching components...")
        component_dir = self.openemis_path / "src" / "Controller" / "Component"
        if component_dir.exists():
            # Always include NavigationComponent
            nav_component = component_dir / "NavigationComponent.php"
            if nav_component.exists():
                print(f"      ✓ Found NavigationComponent.php")
                all_files.append(nav_component)

            # Search for keyword matches
            for keyword in keywords:
                matches = list(component_dir.rglob(f"*{keyword}*.php"))
                if matches:
                    print(f"      ✓ {len(matches)} components")
                all_files.extend(matches)

        # 4. JavaScript files
        print(f"\n   📂 Searching JavaScript...")
        js_dir = self.openemis_path / "webroot" / "js"
        if js_dir.exists():
            for keyword in keywords:
                matches = list(js_dir.rglob(f"*{keyword}*.js"))
                if matches:
                    print(f"      ✓ {len(matches)} JS files")
                all_files.extend(matches[:3])  # Limit JS files

        # 5. src/Template (CakePHP 3 style)
        template_dir = self.openemis_path / "src" / "Template"
        if template_dir.exists():
            for keyword in keywords:
                matches = list(template_dir.rglob(f"*{keyword}*.php"))
                if matches:
                    print(f"      ✓ {len(matches)} in src/Template")
                all_files.extend(matches)

        # Deduplicate and sort by relevance
        all_files = list(set(all_files))
        all_files.sort(key=lambda f: self._file_relevance(f, keywords), reverse=True)

        return all_files[:10]  # Top 10 most relevant

    def _file_relevance(self, file: Path, keywords: List[str]) -> int:
        """Score file relevance."""
        score = 0
        filename_lower = file.name.lower()

        # Exact match
        for keyword in keywords:
            if keyword == filename_lower.replace('.php', '').replace('.js', ''):
                score += 100

        # Partial match
        for keyword in keywords:
            if keyword in filename_lower:
                score += 10

        # Bonus for important files
        if 'navigation' in filename_lower.lower():
            score += 50
        if 'component' in str(file).lower():
            score += 30
        if 'controller' in str(file).lower():
            score += 20

        return score

    def _extract_selectors(self, files: List[Path]) -> Dict:
        """Extract selectors from all file types."""
        selectors = {
            "ids": [],
            "classes": [],
            "names": [],
            "types": [],
            "data_attrs": [],
            "navigation_items": [],
            "file_contexts": []
        }

        for file in files:
            try:
                rel_path = file.relative_to(self.openemis_path)
                print(f"\n   📄 {rel_path}")

                content = file.read_text(encoding='utf-8', errors='ignore')

                # Extract HTML selectors
                ids = re.findall(r'id=["\']([^"\']+)["\']', content)
                classes = re.findall(r'class=["\']([^"\']+)["\']', content)
                names = re.findall(r'name=["\']([^"\']+)["\']', content)
                types = re.findall(r'type=["\']([^"\']+)["\']', content)

                # Extract data attributes
                data_attrs = re.findall(r'data-([a-z-]+)=["\']([^"\']+)["\']', content)

                # Extract navigation items (from NavigationComponent)
                if 'navigation' in file.name.lower():
                    nav_items = self._extract_navigation_items(content)
                    selectors["navigation_items"].extend(nav_items)
                    print(f"      ✓ {len(nav_items)} navigation items")

                # Add to selectors
                selectors["ids"].extend([f"#{id}" for id in ids])
                selectors["classes"].extend([f".{cls}" for class_str in classes
                                             for cls in class_str.split()
                                             if cls and not cls.startswith('<')])
                selectors["names"].extend([f"[name='{name}']" for name in names])
                selectors["types"].extend([f"[type='{t}']" for t in types])
                selectors["data_attrs"].extend([f"[data-{attr}='{val}']"
                                                for attr, val in data_attrs])

                print(f"      IDs: {len(ids)}, Classes: {len(classes)}, Names: {len(names)}")

                selectors["file_contexts"].append({
                    "file": str(rel_path),
                    "type": self._get_file_type(file),
                    "selectors_count": len(ids) + len(names)
                })

            except Exception as e:
                print(f"      ✗ Error: {e}")

        # Deduplicate
        for key in ["ids", "classes", "names", "types", "data_attrs"]:
            selectors[key] = list(set(selectors[key]))

        return selectors

    def _extract_navigation_items(self, content: str) -> List[str]:
        """Extract navigation items from NavigationComponent."""
        nav_items = []

        # Pattern: 'label' => __('Students')
        labels = re.findall(r"['\"]label['\"] => __\(['\"]([^'\"]+)['\"]\)", content)
        nav_items.extend(labels)

        # Pattern: 'url' => ['controller' => 'Students', 'action' => 'index']
        urls = re.findall(r"['\"]controller['\"] => ['\"]([^'\"]+)['\"]", content)
        nav_items.extend([f"nav-{url.lower()}" for url in urls])

        return nav_items

    def _get_file_type(self, file: Path) -> str:
        """Determine file type."""
        file_str = str(file).lower()
        if '/templates/' in file_str or file_str.endswith('.ctp'):
            return 'template'
        elif '/controller/' in file_str:
            return 'controller'
        elif '/component/' in file_str:
            return 'component'
        elif file_str.endswith('.js'):
            return 'javascript'
        else:
            return 'other'

    def format_for_prompt(self, selectors: Dict) -> str:
        """Format selectors for LLM prompt."""
        if not any(selectors.get(k) for k in ["ids", "names", "classes", "navigation_items"]):
            return "⚠️  No selectors found"

        lines = ["\nAVAILABLE SELECTORS FROM OPENEMIS SOURCE CODE:"]
        lines.append("=" * 70)

        # All available selectors
        if selectors.get("ids"):
            lines.append(f"\nIDs ({len(selectors['ids'])} total):")
            lines.append(f"   {', '.join(selectors['ids'][:15])}")

        if selectors.get("names"):
            lines.append(f"\nName attributes ({len(selectors['names'])} total):")
            lines.append(f"   {', '.join(selectors['names'][:15])}")

        if selectors.get("navigation_items"):
            lines.append(f"\nNavigation items ({len(selectors['navigation_items'])} total):")
            lines.append(f"   {', '.join(selectors['navigation_items'][:10])}")

        # File sources
        if selectors.get("file_contexts"):
            lines.append(f"\nFound in ({len(selectors['file_contexts'])} files):")
            for ctx in selectors['file_contexts'][:5]:
                lines.append(f"   • {ctx['file']} ({ctx['type']}, {ctx['selectors_count']} selectors)")

        lines.append("=" * 70)
        return "\n".join(lines)


# Singleton
_analyzer = None


def get_code_analyzer(openemis_path: str = None) -> CodeAnalyzer:
    """Get or create CodeAnalyzer instance."""
    global _analyzer
    if _analyzer is None:
        if openemis_path is None:
            # Try common paths
            possible_paths = [
                "/openemis-core",
                "~/ai_tools/openemis-core",
                os.getenv("OPENEMIS_SOURCE_PATH", ""),
            ]
            for path in possible_paths:
                if path:
                    expanded = os.path.expanduser(path)
                    if os.path.exists(expanded):
                        openemis_path = expanded
                        break

        _analyzer = CodeAnalyzer(openemis_path)

    return _analyzer
