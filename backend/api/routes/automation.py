"""
Automation Routes - Execute Automations

Core automation execution endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid

from backend.models.api_schemas import AutomationRequest, AutomationResponse
from backend.models.auth import User
from backend.models.learning import LearningExample
from backend.api.dependencies import require_authenticated
from backend.core.automation_engine import execute_automation
from backend.core.llm_client import LLMClient
from backend.core.learning_store import get_learning_store
from backend.core.prompt_manager import get_prompt_manager
from backend.config import settings


router = APIRouter(prefix="/automation", tags=["Automation"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/execute", response_model=AutomationResponse)
@limiter.limit("10/minute")  # 10 automations per minute per IP
async def execute_automation_endpoint(
    request: Request,
    automation_req: AutomationRequest,
    user: User = Depends(require_authenticated)
):
    """
    Execute an automation task.

    Steps:
    1. Find similar examples from learning store
    2. Build enhanced prompt with examples
    3. Request structured commands from LLM
    4. Execute commands safely
    5. Save successful execution to learning store

    Rate Limit: 10 requests per minute per IP

    Returns:
        Automation result with execution details

    Raises:
        400: If task description is invalid
        500: If execution fails
    """
    task_id = str(uuid.uuid4())

    try:
        # Get dependencies
        llm_client = LLMClient(server_url=settings.LLM_SERVER_URL)
        learning_store = get_learning_store()
        prompt_manager = get_prompt_manager()

        # Find similar examples for few-shot learning
        similar_examples = await learning_store.find_similar(
            automation_req.task_description,
            limit=3
        )

        # Build enhanced prompt with examples
        system_prompt = prompt_manager.build_enhanced_prompt(similar_examples)

        # Generate commands from LLM
        commands = await llm_client.generate_commands(
            user_intent=automation_req.task_description,
            system_prompt=system_prompt,
            examples=[ex.model_dump() for ex in similar_examples]
        )

        # Serialize commands for response
        commands_json = [cmd.model_dump() for cmd in commands]

        # Execute if auto_execute is True
        if automation_req.auto_execute:
            result = await execute_automation(commands, headless=False)

            # Save successful execution to learning store
            if result.success:
                example = LearningExample(
                    task_description=automation_req.task_description,
                    user_intent=automation_req.task_description,
                    commands=commands_json,
                    success=True,
                    context=automation_req.context or {},
                    execution_time_ms=result.execution_time_ms,
                    tags=[]  # TODO: Auto-generate tags
                )
                await learning_store.save_example(example)

            return AutomationResponse(
                task_id=task_id,
                commands=commands_json,
                executed=True,
                result=result.to_dict()
            )
        else:
            # Just return commands without executing
            return AutomationResponse(
                task_id=task_id,
                commands=commands_json,
                executed=False,
                result=None
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Automation failed: {str(e)}"
        )


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    user: User = Depends(require_authenticated)
):
    """
    Get status of an automation task.

    Note: Current implementation executes synchronously, so status is immediate.
    This endpoint is provided for future async execution support.
    """
    # TODO: Implement task tracking for async execution
    return {
        "task_id": task_id,
        "status": "completed",
        "message": "Task execution is currently synchronous"
    }
