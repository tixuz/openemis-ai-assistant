# test_prompts.py

import asyncio
from backend.core.llm_client import LLMClient


async def test_prompt():
    client = LLMClient()

    # Test cases
    test_cases = [
        "Login to OpenEMIS as admin",
        "mark attendance, john absent",
        "go to institution P1002",
        "search for student 12345",
    ]

    for task in test_cases:
        print(f"\n{'=' * 60}")
        print(f"Task: {task}")
        print(f"{'=' * 60}")

        try:
            commands = await client.generate_commands(task)
            print(f"✅ Success! Generated {len(commands)} commands:")
            for i, cmd in enumerate(commands, 1):
                print(f"  {i}. {cmd['type']}: {cmd}")
        except Exception as e:
            print(f"❌ Failed: {e}")

        print()


asyncio.run(test_prompt())