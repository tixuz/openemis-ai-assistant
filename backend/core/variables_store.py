"""
Variables Store

Stores and retrieves user variables (key-value pairs).
Uses JSON format for simple structure.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from backend.models.variables import UserVariable


class VariablesStore:
    """
    Manages user variables storage.

    Each user has a variables file:
    data/variables/{username}/variables.json
    """

    def __init__(self, base_dir: str = "data/variables"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_variables_file(self, username: str) -> Path:
        """Get the variables file path for a specific user"""
        user_dir = self.base_dir / username
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / "variables.json"

    def _load_variables(self, username: str) -> Dict[str, UserVariable]:
        """Load all variables for a user as a dict"""
        file_path = self._get_user_variables_file(username)

        if not file_path.exists():
            return {}

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Convert to UserVariable objects
            variables = {}
            for var_data in data.get("variables", []):
                var = UserVariable(**var_data)
                variables[var.key] = var

            return variables
        except Exception as e:
            print(f"Error loading variables for {username}: {e}")
            return {}

    def _save_variables(self, username: str, variables: Dict[str, UserVariable]):
        """Save all variables for a user"""
        file_path = self._get_user_variables_file(username)

        data = {
            "variables": [var.model_dump() for var in variables.values()],
            "updated_at": datetime.utcnow().isoformat()
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    async def get_all_variables(self, username: str) -> List[UserVariable]:
        """Get all variables for a user"""
        variables = self._load_variables(username)
        return list(variables.values())

    async def get_variable(self, username: str, key: str) -> Optional[UserVariable]:
        """Get a specific variable by key"""
        variables = self._load_variables(username)
        return variables.get(key)

    async def set_variable(
        self,
        username: str,
        key: str,
        value: str,
        description: Optional[str] = None,
        var_type: str = "text"
    ) -> UserVariable:
        """Create or update a variable"""
        variables = self._load_variables(username)

        # Check if updating existing variable
        if key in variables:
            var = variables[key]
            var.value = value
            var.updated_at = datetime.utcnow().isoformat()
            if description is not None:
                var.description = description
            if var_type:
                var.type = var_type
        else:
            # Create new variable
            var = UserVariable(
                key=key,
                value=value,
                description=description,
                type=var_type
            )
            variables[key] = var

        # Save all variables
        self._save_variables(username, variables)

        return var

    async def delete_variable(self, username: str, key: str) -> bool:
        """Delete a variable"""
        variables = self._load_variables(username)

        if key in variables:
            del variables[key]
            self._save_variables(username, variables)
            return True

        return False

    async def get_variables_dict(self, username: str) -> Dict[str, str]:
        """
        Get all variables as a simple dict for substitution.

        Returns: {"username": "admin", "password": "demo123", ...}
        """
        variables = self._load_variables(username)
        return {key: var.value for key, var in variables.items()}

    async def substitute_variables(
        self,
        username: str,
        text: str
    ) -> str:
        """
        Substitute variables in text.

        Example: "Login with {username} and {password}"
                 -> "Login with admin and demo123"
        """
        variables = await self.get_variables_dict(username)

        result = text
        for key, value in variables.items():
            # Replace {key} with value
            result = result.replace(f"{{{key}}}", value)

        return result

    async def count_variables(self, username: str) -> int:
        """Count total variables for a user"""
        variables = self._load_variables(username)
        return len(variables)


# Global instance
_variables_store = None


def get_variables_store() -> VariablesStore:
    """Get global variables store instance"""
    global _variables_store
    if _variables_store is None:
        _variables_store = VariablesStore()
    return _variables_store
