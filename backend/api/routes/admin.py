"""
Admin Routes - Prompt Engineering and System Management

For admins and prompt engineers to manage the system.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime

from backend.models.api_schemas import (
    PromptUpdate, PromptResponse, ExampleListResponse, AnalyticsResponse
)
from backend.models.auth import User
from backend.models.learning import LearningExample
from backend.api.dependencies import require_admin, require_prompt_engineer
from backend.core.learning_store import get_learning_store
from backend.core.prompt_manager import get_prompt_manager
from backend.config import settings


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/prompts", response_model=PromptResponse)
async def get_system_prompt(
    user: User = Depends(require_prompt_engineer)
):
    """
    Get current system prompt.

    Requires: prompt_engineer or admin role
    """
    prompt_manager = get_prompt_manager()
    content = prompt_manager.load_system_prompt()

    return PromptResponse(
        content=content,
        updated_at=datetime.utcnow().isoformat()
    )


@router.post("/prompts", response_model=PromptResponse)
async def update_system_prompt(
    prompt: PromptUpdate,
    user: User = Depends(require_prompt_engineer)
):
    """
    Update system prompt.

    Requires: prompt_engineer or admin role

    Args:
        prompt: New prompt content

    Returns:
        Updated prompt confirmation
    """
    prompt_manager = get_prompt_manager()

    try:
        prompt_manager.save_system_prompt(prompt.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {e}")

    return PromptResponse(
        content=prompt.content,
        updated_at=datetime.utcnow().isoformat()
    )


@router.get("/examples", response_model=ExampleListResponse)
async def list_examples(
    user: User = Depends(require_prompt_engineer),
    limit: int = 100,
    tags: str | None = None
):
    """
    List all learning examples.

    Requires: prompt_engineer or admin role

    Args:
        limit: Max number of examples to return
        tags: Comma-separated tags to filter by

    Returns:
        List of learning examples
    """
    learning_store = get_learning_store()

    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        examples = await learning_store.get_by_tags(tag_list)
    else:
        examples = await learning_store.get_all_examples()

    # Limit results
    examples = examples[:limit]

    # Convert to dict
    examples_data = [ex.model_dump() for ex in examples]

    total = await learning_store.count()

    return ExampleListResponse(
        examples=examples_data,
        total=total
    )


@router.get("/examples/{example_id}")
async def get_example(
    example_id: str,
    user: User = Depends(require_prompt_engineer)
):
    """
    Get a specific learning example by ID.

    Requires: prompt_engineer or admin role
    """
    learning_store = get_learning_store()
    example = await learning_store.get_by_id(example_id)

    if not example:
        raise HTTPException(status_code=404, detail="Example not found")

    return example.model_dump()


@router.delete("/examples/{example_id}")
async def delete_example(
    example_id: str,
    user: User = Depends(require_admin)  # Only admins can delete
):
    """
    Delete a learning example.

    Requires: admin role

    Args:
        example_id: ID of example to delete

    Returns:
        Success message
    """
    learning_store = get_learning_store()
    success = await learning_store.delete_example(example_id)

    if not success:
        raise HTTPException(status_code=404, detail="Example not found")

    return {"message": "Example deleted successfully"}


@router.post("/examples", status_code=201)
async def create_example(
    example: LearningExample,
    user: User = Depends(require_prompt_engineer)
):
    """
    Manually add a learning example.

    Requires: prompt_engineer or admin role

    Args:
        example: Learning example to add

    Returns:
        Created example
    """
    learning_store = get_learning_store()

    try:
        example_id = await learning_store.save_example(example)
        return {"id": example_id, "message": "Example created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create example: {e}")


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user: User = Depends(require_prompt_engineer)
):
    """
    Get system analytics and usage statistics.

    Requires: prompt_engineer or admin role

    Returns:
        Analytics data including success rates and performance metrics
    """
    learning_store = get_learning_store()
    examples = await learning_store.get_all_examples()

    if not examples:
        return AnalyticsResponse(
            total_executions=0,
            success_rate=0.0,
            avg_execution_time_ms=0.0,
            total_examples=0,
            recent_tasks=[]
        )

    # Calculate stats
    successful = [ex for ex in examples if ex.success]
    success_rate = len(successful) / len(examples) if examples else 0.0

    # Average execution time
    exec_times = [ex.execution_time_ms for ex in examples if ex.execution_time_ms > 0]
    avg_time = sum(exec_times) / len(exec_times) if exec_times else 0.0

    # Recent tasks
    recent = sorted(examples, key=lambda x: x.timestamp, reverse=True)[:10]
    recent_tasks = [
        {
            "task": ex.task_description,
            "success": ex.success,
            "timestamp": ex.timestamp,
            "execution_time_ms": ex.execution_time_ms
        }
        for ex in recent
    ]

    return AnalyticsResponse(
        total_executions=len(examples),
        success_rate=success_rate,
        avg_execution_time_ms=avg_time,
        total_examples=len(examples),
        recent_tasks=recent_tasks
    )


@router.post("/test")
async def test_automation(
    task: str,
    user: User = Depends(require_prompt_engineer)
):
    """
    Test automation generation without executing.

    Useful for prompt engineering and testing.

    Requires: prompt_engineer or admin role

    Args:
        task: Task description to test

    Returns:
        Generated commands (not executed)
    """
    from backend.core.llm_client import LLMClient

    llm_client = LLMClient(server_url=settings.LLM_SERVER_URL)
    learning_store = get_learning_store()
    prompt_manager = get_prompt_manager()

    # Find examples
    examples = await learning_store.find_similar(task, limit=3)

    # Build prompt
    system_prompt = prompt_manager.build_enhanced_prompt(examples)

    try:
        # Generate commands
        commands = await llm_client.generate_commands(
            user_intent=task,
            system_prompt=system_prompt,
            examples=[ex.model_dump() for ex in examples]
        )

        return {
            "task": task,
            "commands": [cmd.model_dump() for cmd in commands],
            "examples_used": len(examples)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {e}")
