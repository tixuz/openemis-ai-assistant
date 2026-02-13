"""
Learning Store - Save and Retrieve Successful Automation Examples

This enables the AI to learn from past successes through few-shot learning.
Simple JSONL file storage (can be upgraded to vector search later).
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio

from backend.models.learning import LearningExample


class LearningStore:
    """
    Store for successful automation examples.

    Uses JSONL format for simple, append-only storage.
    Can be upgraded to vector database for semantic search later.
    """

    def __init__(self, file_path: str = "data/learning/examples.jsonl"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache for faster retrieval
        self._cache: Optional[List[LearningExample]] = None
        self._cache_lock = asyncio.Lock()

    async def save_example(self, example: LearningExample) -> str:
        """
        Save a successful automation example.

        Args:
            example: LearningExample to save

        Returns:
            Example ID
        """
        # Append to file
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_example, example)

        # Invalidate cache
        async with self._cache_lock:
            self._cache = None

        return example.id

    def _write_example(self, example: LearningExample):
        """Write example to JSONL file (synchronous)"""
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(example.model_dump_json() + "\n")

    async def find_similar(
        self,
        query: str,
        limit: int = 5,
        tags: Optional[List[str]] = None
    ) -> List[LearningExample]:
        """
        Find examples similar to the query.

        Uses simple keyword matching for now.
        Can be upgraded to vector similarity search later.

        Args:
            query: Search query (user intent)
            limit: Max number of examples to return
            tags: Optional filter by tags

        Returns:
            List of relevant examples, sorted by relevance
        """
        examples = await self.get_all_examples()

        if not examples:
            return []

        # Filter by tags if provided
        if tags:
            examples = [
                ex for ex in examples
                if any(tag in ex.tags for tag in tags)
            ]

        # Calculate relevance scores based on keyword overlap
        query_words = set(query.lower().split())
        scored = []

        for ex in examples:
            # Combine task description and user intent for matching
            text = f"{ex.task_description} {ex.user_intent}".lower()
            text_words = set(text.split())

            # Count keyword overlaps
            overlap = len(query_words & text_words)

            if overlap > 0:
                scored.append((overlap, ex))

        # Sort by score (descending)
        scored.sort(reverse=True, key=lambda x: x[0])

        # Return top N
        return [ex for score, ex in scored[:limit]]

    async def get_all_examples(self) -> List[LearningExample]:
        """
        Load all examples from file.

        Uses in-memory cache for performance.
        """
        async with self._cache_lock:
            if self._cache is None:
                loop = asyncio.get_event_loop()
                self._cache = await loop.run_in_executor(None, self._load_examples)

        return self._cache

    def _load_examples(self) -> List[LearningExample]:
        """Load examples from JSONL file (synchronous)"""
        if not self.file_path.exists():
            return []

        examples = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    example = LearningExample(**data)
                    examples.append(example)
                except (json.JSONDecodeError, ValueError) as e:
                    # Skip malformed lines
                    print(f"Warning: Skipping malformed example: {e}")
                    continue

        return examples

    async def get_by_id(self, example_id: str) -> Optional[LearningExample]:
        """Get an example by ID"""
        examples = await self.get_all_examples()
        for ex in examples:
            if ex.id == example_id:
                return ex
        return None

    async def get_by_tags(self, tags: List[str]) -> List[LearningExample]:
        """Get all examples with any of the given tags"""
        examples = await self.get_all_examples()
        return [
            ex for ex in examples
            if any(tag in ex.tags for tag in tags)
        ]

    async def count(self) -> int:
        """Get total number of examples"""
        examples = await self.get_all_examples()
        return len(examples)

    async def clear_cache(self):
        """Clear the in-memory cache"""
        async with self._cache_lock:
            self._cache = None

    async def delete_example(self, example_id: str) -> bool:
        """
        Delete an example by ID.

        Note: This rewrites the entire file, which is slow for large files.
        Consider archiving instead for production.
        """
        examples = await self.get_all_examples()
        filtered = [ex for ex in examples if ex.id != example_id]

        if len(filtered) == len(examples):
            return False  # Not found

        # Rewrite file
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._rewrite_file, filtered)

        # Clear cache
        await self.clear_cache()

        return True

    def _rewrite_file(self, examples: List[LearningExample]):
        """Rewrite entire JSONL file (synchronous)"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(ex.model_dump_json() + "\n")


# Module-level instance for convenience
_default_store: Optional[LearningStore] = None


def get_learning_store(file_path: str = "data/learning/examples.jsonl") -> LearningStore:
    """Get or create the default learning store instance"""
    global _default_store
    if _default_store is None or _default_store.file_path != Path(file_path):
        _default_store = LearningStore(file_path)
    return _default_store
