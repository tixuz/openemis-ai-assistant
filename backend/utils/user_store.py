"""
User Store - Simple JSON-based User Storage

For production, consider migrating to PostgreSQL or another database.
"""
import json
from pathlib import Path
from typing import Optional, List, Dict
from backend.models.auth import User, UserInDB
from backend.utils.security import get_password_hash


class UserStore:
    """Simple file-based user storage"""

    def __init__(self, file_path: str = "data/users.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize with default admin if file doesn't exist
        if not self.file_path.exists():
            self._create_default_users()

    def _create_default_users(self):
        """Create default admin user"""
        default_users = [
            {
                "username": "admin",
                "email": "admin@openemis.local",
                "full_name": "Administrator",
                "role": "admin",
                "permissions": ["all"],
                "disabled": False,
                "hashed_password": get_password_hash("admin123")  # Change in production!
            }
        ]

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=2)

    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        users = self._load_users()
        for user_data in users:
            if user_data["username"].lower() == username.lower():
                return UserInDB(**user_data)
        return None

    def create_user(self, user: UserInDB) -> bool:
        """Create a new user"""
        users = self._load_users()

        # Check if username exists
        if any(u["username"].lower() == user.username.lower() for u in users):
            return False

        # Add user
        users.append(user.model_dump())
        self._save_users(users)
        return True

    def update_user(self, username: str, updates: Dict) -> bool:
        """Update user data"""
        users = self._load_users()

        for i, user_data in enumerate(users):
            if user_data["username"].lower() == username.lower():
                user_data.update(updates)
                users[i] = user_data
                self._save_users(users)
                return True

        return False

    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        users = self._load_users()
        filtered = [u for u in users if u["username"].lower() != username.lower()]

        if len(filtered) == len(users):
            return False  # User not found

        self._save_users(filtered)
        return True

    def list_users(self) -> List[User]:
        """List all users (without passwords)"""
        users = self._load_users()
        return [User(**{k: v for k, v in u.items() if k != "hashed_password"}) for u in users]

    def _load_users(self) -> List[Dict]:
        """Load users from JSON file"""
        if not self.file_path.exists():
            return []

        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_users(self, users: List[Dict]):
        """Save users to JSON file"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)


# Module-level instance
_default_store: Optional[UserStore] = None


def get_user_store(file_path: str = "data/users.json") -> UserStore:
    """Get or create the default user store instance"""
    global _default_store
    if _default_store is None or _default_store.file_path != Path(file_path):
        _default_store = UserStore(file_path)
    return _default_store
