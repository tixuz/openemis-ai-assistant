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
from backend.models.llm_config import LLMProviderConfig, get_llm_config_store
from backend.models.auth import User
from backend.models.learning import LearningExample
from backend.api.dependencies import require_admin, require_prompt_engineer, require_authenticated
from backend.core.learning_store import get_learning_store
from backend.core.prompt_manager import get_prompt_manager
from backend.core.history_store import get_history_store
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

# LLM Configuration Management

@router.get("/llm-config")
async def get_llm_config(
    user: User = Depends(require_admin)
):
    """
    Get current LLM provider configuration.

    Requires: admin role
    
    Returns current provider type and settings (API keys are masked).
    """
    config_store = get_llm_config_store()
    config = config_store.load_config()
    
    # Mask API key for security
    config_dict = config.model_dump()
    if config_dict.get("api_key"):
        config_dict["api_key"] = "***" + config_dict["api_key"][-4:] if len(config_dict["api_key"]) > 4 else "***"
    
    return config_dict


@router.post("/llm-config")
async def update_llm_config(
    config: LLMProviderConfig,
    user: User = Depends(require_admin)
):
    """
    Update LLM provider configuration.

    Requires: admin role
    
    Saves new provider settings including API keys (encrypted).
    """
    config_store = get_llm_config_store()
    config_store.save_config(config)
    
    return {
        "success": True,
        "message": f"LLM provider updated to: {config.provider}",
        "provider": config.provider
    }


@router.post("/llm-config/test")
async def test_llm_config(
    config: LLMProviderConfig,
    user: User = Depends(require_admin)
):
    """
    Test LLM provider connection.

    Requires: admin role
    
    Tests connectivity without saving configuration.
    """
    from backend.core.llm_providers import LLMProviderFactory
    
    try:
        # Create provider from config
        provider = LLMProviderFactory.create_provider(
            provider_type=config.provider,
            config=config.get_provider_dict()
        )
        
        # Test connection
        is_connected = provider.test_connection()
        
        if is_connected:
            return {
                "success": True,
                "message": f"Successfully connected to {config.provider}",
                "provider": config.provider
            }
        else:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to {config.provider}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )


@router.get("/llm-config/providers")
async def list_llm_providers(
    user: User = Depends(require_admin)
):
    """
    List available LLM providers with their default models.

    Requires: admin role
    """
    return {
        "providers": [
            {
                "id": "local",
                "name": "Local LLM",
                "description": "Self-hosted LLM server (llama.cpp)",
                "requires_api_key": False,
                "default_model": None,
                "models": ["Custom model on your server"]
            },
            {
                "id": "claude",
                "name": "Claude (Anthropic)",
                "description": "Anthropic's Claude AI models",
                "requires_api_key": True,
                "default_model": "claude-3-5-sonnet-20241022",
                "models": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022",
                    "claude-opus-4",
                    "claude-3-opus-20240229"
                ]
            },
            {
                "id": "gemini",
                "name": "Gemini (Google)",
                "description": "Google's Gemini AI models",
                "requires_api_key": True,
                "default_model": "gemini-2.0-flash",
                "models": [
                    "gemini-2.0-flash",
                    "gemini-2.5-flash",
                    "gemini-2.5-pro"
                ]
            },
            {
                "id": "openai",
                "name": "ChatGPT (OpenAI)",
                "description": "OpenAI's GPT models",
                "requires_api_key": True,
                "default_model": "gpt-4o-mini",
                "models": [
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo"
                ]
            }
        ]
    }


@router.get("/script-history")
async def get_script_execution_history(
    user: User = Depends(require_authenticated),
    limit: int = 100,
    offset: int = 0,
    load_screenshots: bool = False
):
    """
    Get script execution history (from scripts branch).

    Available to all authenticated users (shows their own history).
    Admins can see all users' history by specifying username parameter.

    Args:
        limit: Max number of history items (default: 100)
        offset: Pagination offset (default: 0)
        load_screenshots: Load screenshot base64 data (default: False)

    Returns:
        Dictionary with history list and total count
    """
    history_store = get_history_store()

    # Get user's script execution history from scripts branch
    messages = await history_store.get_user_history(
        username=user.username,
        limit=limit,
        offset=offset,
        branch="scripts"
    )

    # Get total count
    total = await history_store.count_user_messages(user.username)

    # Convert to dict
    history_data = [msg.model_dump() for msg in messages]

    # Optionally load screenshots from scripts branch
    if load_screenshots:
        for item in history_data:
            if item.get("execution_result") and item["execution_result"].get("screenshot_data"):
                screenshot_list = item["execution_result"]["screenshot_data"]
                for screenshot_info in screenshot_list:
                    if "filename" in screenshot_info and "data" not in screenshot_info:
                        filename = screenshot_info["filename"]
                        base64_data = await history_store.load_screenshot(
                            username=user.username,
                            filename=filename,
                            branch="scripts"
                        )
                        if base64_data:
                            screenshot_info["data"] = base64_data

    return {
        "history": history_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }
