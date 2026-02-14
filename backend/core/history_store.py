"""
Chat History Store

Stores and retrieves conversation history per user.
Uses JSONL format for consistency with learning examples.
"""
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from backend.models.history import ChatMessage


class HistoryStore:
    """
    Manages chat history storage.

    Stores each user's history in a separate JSONL file:
    data/history/{user_id}/chat_history.jsonl
    """

    def __init__(self, base_dir: str = "data/history"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_history_file(self, user_id: str) -> Path:
        """Get the history file path for a specific user"""
        user_dir = self.base_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir / "chat_history.jsonl"

    async def save_message(self, message: ChatMessage) -> str:
        """
        Save a chat message to user's history.

        Args:
            message: ChatMessage to save

        Returns:
            Message ID
        """
        file_path = self._get_user_history_file(message.user_id)

        # Append to JSONL file
        with open(file_path, "a") as f:
            f.write(json.dumps(message.model_dump()) + "\n")

        return message.id

    async def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Get chat history for a specific user.

        Args:
            user_id: User's unique identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip (for pagination)

        Returns:
            List of ChatMessage objects, newest first
        """
        file_path = self._get_user_history_file(user_id)

        if not file_path.exists():
            return []

        messages = []
        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    messages.append(ChatMessage(**data))
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing history line: {e}")
                    continue

        # Sort by timestamp (newest first)
        messages.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        start = offset
        end = offset + limit
        return messages[start:end]

    async def get_recent_messages(
        self,
        user_id: str,
        hours: int = 24
    ) -> List[ChatMessage]:
        """
        Get recent messages within the specified time window.

        Args:
            user_id: User's unique identifier
            hours: Number of hours to look back

        Returns:
            List of recent ChatMessage objects
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        all_messages = await self.get_user_history(user_id, limit=1000)

        recent = []
        for msg in all_messages:
            msg_time = datetime.fromisoformat(msg.timestamp)
            if msg_time >= cutoff_time:
                recent.append(msg)

        return recent

    async def count_user_messages(self, user_id: str) -> int:
        """
        Count total messages for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            Total message count
        """
        file_path = self._get_user_history_file(user_id)

        if not file_path.exists():
            return 0

        with open(file_path, "r") as f:
            return sum(1 for _ in f)

    async def delete_user_history(self, user_id: str) -> bool:
        """
        Delete all history for a user.

        Args:
            user_id: User's unique identifier

        Returns:
            True if deleted, False if not found
        """
        user_dir = self.base_dir / user_id
        if user_dir.exists():
            # Delete history file
            history_file = user_dir / "chat_history.jsonl"
            if history_file.exists():
                history_file.unlink()

            # Remove directory if empty
            try:
                user_dir.rmdir()
            except OSError:
                pass  # Directory not empty, that's fine

            return True
        return False

    async def get_message_by_id(
        self,
        user_id: str,
        message_id: str
    ) -> Optional[ChatMessage]:
        """
        Get a specific message by ID.

        Args:
            user_id: User's unique identifier
            message_id: Message ID to find

        Returns:
            ChatMessage if found, None otherwise
        """
        messages = await self.get_user_history(user_id, limit=1000)
        for msg in messages:
            if msg.id == message_id:
                return msg
        return None

    async def get_all_users_with_history(self) -> List[str]:
        """
        Get list of all user IDs that have chat history.

        Returns:
            List of user IDs
        """
        user_ids = []
        for user_dir in self.base_dir.iterdir():
            if user_dir.is_dir():
                user_ids.append(user_dir.name)
        return user_ids


# Global instance
_history_store = None


def get_history_store() -> HistoryStore:
    """Get global history store instance"""
    global _history_store
    if _history_store is None:
        _history_store = HistoryStore()
    return _history_store
