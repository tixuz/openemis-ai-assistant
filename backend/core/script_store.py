"""
Script Store - Reusable Automation Scripts Storage

Manages saved automation scripts with CRUD operations.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.models.scripts import AutomationScript


class ScriptStore:
    """Store and retrieve automation scripts"""

    def __init__(self, file_path: str = "data/scripts/scripts.jsonl"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache for fast lookup
        self._scripts: Dict[str, AutomationScript] = {}
        self._load_cache()

    def _load_cache(self):
        """Load all scripts into memory"""
        if not self.file_path.exists():
            return

        self._scripts.clear()
        with open(self.file_path, "r") as f:
            for line in f:
                if line.strip():
                    script = AutomationScript(**json.loads(line))
                    self._scripts[script.name] = script

    def _save_to_disk(self):
        """Save all scripts to disk"""
        with open(self.file_path, "w") as f:
            for script in self._scripts.values():
                f.write(json.dumps(script.model_dump()) + "\n")

    async def create_script(self, script: AutomationScript) -> str:
        """Create a new script"""
        if script.name in self._scripts:
            raise ValueError(f"Script '{script.name}' already exists")

        self._scripts[script.name] = script
        self._save_to_disk()
        return script.id

    async def update_script(self, script_name: str, script: AutomationScript) -> bool:
        """Update an existing script"""
        if script_name not in self._scripts:
            return False

        # Preserve execution count
        old_script = self._scripts[script_name]
        script.execution_count = old_script.execution_count
        script.updated_at = datetime.utcnow().isoformat()

        # Handle name change
        if script.name != script_name:
            if script.name in self._scripts:
                raise ValueError(f"Script '{script.name}' already exists")
            del self._scripts[script_name]

        self._scripts[script.name] = script
        self._save_to_disk()
        return True

    async def delete_script(self, script_name: str) -> bool:
        """Delete a script"""
        if script_name not in self._scripts:
            return False

        del self._scripts[script_name]
        self._save_to_disk()
        return True

    async def get_script(self, script_name: str) -> Optional[AutomationScript]:
        """Get a script by name"""
        return self._scripts.get(script_name)

    async def get_all_scripts(self, tags: Optional[List[str]] = None) -> List[AutomationScript]:
        """Get all scripts, optionally filtered by tags"""
        scripts = list(self._scripts.values())

        if tags:
            scripts = [
                s for s in scripts
                if any(tag in s.tags for tag in tags)
            ]

        # Sort by name
        scripts.sort(key=lambda x: x.name)
        return scripts

    async def increment_execution_count(self, script_name: str):
        """Increment the execution counter for a script"""
        if script_name in self._scripts:
            self._scripts[script_name].execution_count += 1
            self._save_to_disk()

    async def count(self) -> int:
        """Total number of scripts"""
        return len(self._scripts)

    async def search_scripts(self, query: str) -> List[AutomationScript]:
        """Search scripts by name or description"""
        query_lower = query.lower()
        results = [
            script for script in self._scripts.values()
            if query_lower in script.name.lower() or
               query_lower in script.description.lower()
        ]
        return results


# Singleton instance
_script_store: Optional[ScriptStore] = None


def get_script_store() -> ScriptStore:
    """Get the global script store instance"""
    global _script_store
    if _script_store is None:
        _script_store = ScriptStore()
    return _script_store
