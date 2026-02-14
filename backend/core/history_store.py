"""
Chat History Store

Stores and retrieves conversation history per user.
Uses JSONL format for consistency with learning examples.

Screenshots are saved separately to avoid bloating JSONL files.
"""
import json
import base64
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from backend.models.history import ChatMessage


class HistoryStore:
    """
    Manages history storage with separate branches for chat and scripts.

    Stores each user's history in separate JSONL files by branch:
    - data/history/{username}/chat/history.jsonl
    - data/history/{username}/scripts/history.jsonl

    Screenshots are stored in branch-specific directories:
    - data/history/{username}/chat/images/
    - data/history/{username}/scripts/images/
    """

    def __init__(self, base_dir: str = "data/history"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_history_file(self, username: str, branch: str = "chat") -> Path:
        """
        Get the history file path for a specific user and branch.

        Args:
            username: Username (unique identifier)
            branch: History branch - "chat" or "scripts" (default: "chat")

        Returns:
            Path to history JSONL file
        """
        branch_dir = self.base_dir / username / branch
        branch_dir.mkdir(parents=True, exist_ok=True)
        return branch_dir / "history.jsonl"

    def _get_user_images_dir(self, username: str, branch: str = "chat") -> Path:
        """
        Get the images directory for a specific user and branch.

        Args:
            username: Username (unique identifier)
            branch: History branch - "chat" or "scripts" (default: "chat")

        Returns:
            Path to images directory
        """
        images_dir = self.base_dir / username / branch / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        return images_dir

    def _save_screenshot(
        self,
        username: str,
        screenshot_data: str,
        timestamp: str,
        branch: str = "chat"
    ) -> str:
        """
        Save screenshot as PNG file and return filename.

        Args:
            username: Username (unique identifier)
            screenshot_data: Base64-encoded PNG data
            timestamp: ISO timestamp for filename
            branch: History branch - "chat" or "scripts" (default: "chat")

        Returns:
            Filename of saved screenshot
        """
        images_dir = self._get_user_images_dir(username, branch)

        # Create filename: {timestamp}_screenshot.png
        # Convert ISO timestamp to safe filename format
        safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
        filename = f"{safe_timestamp}_screenshot.png"
        filepath = images_dir / filename

        # Decode and save PNG
        try:
            image_bytes = base64.b64decode(screenshot_data)
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            return filename
        except Exception as e:
            print(f"Error saving screenshot: {e}")
            return None

    async def save_message(
        self,
        message: ChatMessage,
        branch: str = "chat"
    ) -> str:
        """
        Save a message to user's history in the specified branch.
        Screenshots are extracted and saved as separate PNG files.

        Args:
            message: ChatMessage to save
            branch: History branch - "chat" or "scripts" (default: "chat")

        Returns:
            Message ID
        """
        # Extract and save screenshots separately
        if message.execution_result and "screenshot_data" in message.execution_result:
            screenshot_data_list = message.execution_result.get("screenshot_data", [])

            if screenshot_data_list:
                # Save each screenshot as PNG file in branch-specific directory
                saved_filenames = []
                for screenshot_info in screenshot_data_list:
                    if "data" in screenshot_info:
                        filename = self._save_screenshot(
                            username=message.username,
                            screenshot_data=screenshot_info["data"],
                            timestamp=message.timestamp,
                            branch=branch
                        )
                        if filename:
                            saved_filenames.append(filename)

                # Replace base64 data with just filenames
                message.execution_result["screenshot_data"] = [
                    {"filename": fname} for fname in saved_filenames
                ]

        file_path = self._get_user_history_file(message.username, branch)

        # Append to JSONL file (without base64 screenshot data)
        with open(file_path, "a") as f:
            f.write(json.dumps(message.model_dump()) + "\n")

        return message.id

    async def get_user_history(
        self,
        username: str,
        limit: int = 50,
        offset: int = 0,
        branch: str = "chat"
    ) -> List[ChatMessage]:
        """
        Get history for a specific user from a specific branch.

        Args:
            username: Username (unique identifier)
            limit: Maximum number of messages to return
            offset: Number of messages to skip (for pagination)
            branch: History branch - "chat" or "scripts" (default: "chat")

        Returns:
            List of ChatMessage objects, newest first
        """
        file_path = self._get_user_history_file(username, branch)

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
        username: str,
        hours: int = 24,
        branch: str = "chat"
    ) -> List[ChatMessage]:
        """
        Get recent messages within the specified time window from a specific branch.

        Args:
            username: Username (unique identifier)
            hours: Number of hours to look back
            branch: History branch - "chat" or "scripts" (default: "chat")

        Returns:
            List of recent ChatMessage objects
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        all_messages = await self.get_user_history(username, limit=1000, branch=branch)

        recent = []
        for msg in all_messages:
            msg_time = datetime.fromisoformat(msg.timestamp)
            if msg_time >= cutoff_time:
                recent.append(msg)

        return recent

    async def count_user_messages(self, username: str) -> int:
        """
        Count total messages for a user.

        Args:
            username: Username (unique identifier)

        Returns:
            Total message count
        """
        file_path = self._get_user_history_file(username)

        if not file_path.exists():
            return 0

        with open(file_path, "r") as f:
            return sum(1 for _ in f)

    async def delete_user_history(self, username: str, branch: Optional[str] = None) -> bool:
        """
        Delete history for a user. Can delete specific branch or all branches.

        Args:
            username: Username (unique identifier)
            branch: Specific branch to delete ("chat" or "scripts"), or None to delete all

        Returns:
            True if deleted, False if not found
        """
        import shutil

        user_dir = self.base_dir / username
        if not user_dir.exists():
            return False

        if branch:
            # Delete specific branch
            branch_dir = user_dir / branch
            if branch_dir.exists():
                shutil.rmtree(branch_dir)
                return True
            return False
        else:
            # Delete all branches for this user
            if user_dir.exists():
                shutil.rmtree(user_dir)
                return True
            return False

    async def get_message_by_id(
        self,
        username: str,
        message_id: str
    ) -> Optional[ChatMessage]:
        """
        Get a specific message by ID.

        Args:
            username: Username (unique identifier)
            message_id: Message ID to find

        Returns:
            ChatMessage if found, None otherwise
        """
        messages = await self.get_user_history(username, limit=1000)
        for msg in messages:
            if msg.id == message_id:
                return msg
        return None

    async def load_screenshot(
        self,
        username: str,
        filename: str,
        branch: str = "chat"
    ) -> Optional[str]:
        """
        Load a screenshot from a specific branch and return as base64 string.

        Args:
            username: Username (unique identifier)
            filename: Screenshot filename
            branch: History branch - "chat" or "scripts" (default: "chat")

        Returns:
            Base64-encoded PNG data, or None if not found
        """
        images_dir = self._get_user_images_dir(username, branch)
        filepath = images_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, "rb") as f:
                image_bytes = f.read()
                return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error loading screenshot {filename}: {e}")
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
