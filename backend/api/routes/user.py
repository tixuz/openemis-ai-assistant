"""
User Routes - Chat Interface for End Users

Provides simple chat interface for teachers and OpenEMIS users.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.models.api_schemas import ChatRequest, ChatResponse
from backend.models.auth import User
from backend.api.dependencies import require_authenticated
from backend.core.automation_engine import execute_automation
from backend.core.llm_client import LLMClient
from backend.core.learning_store import get_learning_store
from backend.core.prompt_manager import get_prompt_manager
from backend.models.learning import LearningExample
from backend.config import settings


router = APIRouter(prefix="/user", tags=["User"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # 20 chat messages per minute
async def chat(
    request: Request,
    chat_req: ChatRequest,
    user: User = Depends(require_authenticated)
):
    """
    Chat with AI assistant.

    Automatically determines if the message is a command to execute or just a question.

    Action keywords: "run", "execute", "perform", "do", "click", "fill", "navigate"

    Rate Limit: 20 requests per minute

    Returns:
        Chat response with optional automation execution result
    """
    message = chat_req.message.lower()

    # Determine if this is an action request
    action_keywords = [
        "run", "execute", "perform", "do", "click", "fill",
        "navigate", "go to", "open", "login", "выполни"
    ]
    is_action = any(keyword in message for keyword in action_keywords)

    try:
        # Get dependencies
        llm_client = LLMClient(server_url=settings.LLM_SERVER_URL)
        learning_store = get_learning_store()
        prompt_manager = get_prompt_manager()

        # Find similar examples
        similar_examples = await learning_store.find_similar(chat_req.message, limit=3)

        # Build prompt
        system_prompt = prompt_manager.build_enhanced_prompt(similar_examples)

        if is_action:
            # Generate and execute automation
            commands = await llm_client.generate_commands(
                user_intent=chat_req.message,
                system_prompt=system_prompt,
                examples=[ex.model_dump() for ex in similar_examples]
            )

            # Execute commands (headless=True for Docker environment)
            result = await execute_automation(commands, headless=True)

            # Save successful execution
            if result.success:
                example = LearningExample(
                    task_description=chat_req.message,
                    user_intent=chat_req.message,
                    commands=[cmd.model_dump() for cmd in commands],
                    success=True,
                    context=chat_req.context or {},
                    execution_time_ms=result.execution_time_ms
                )
                await learning_store.save_example(example)

            # Format response
            if result.success:
                response_text = f"✅ Automation completed successfully!\n\n"
                response_text += f"Executed {result.commands_executed} commands in {result.execution_time_ms}ms.\n"
                if result.screenshots:
                    response_text += f"\nScreenshots saved:\n" + "\n".join(f"- {s}" for s in result.screenshots)
            else:
                response_text = f"❌ Automation failed: {result.error}"

            return ChatResponse(
                response=response_text,
                commands_generated=len(commands),
                executed=True,
                execution_result=result.to_dict()
            )
        else:
            # Just a question - return helpful info
            response_text = "I'm an automation assistant for OpenEMIS. "
            response_text += "To execute an automation, use action words like 'run', 'execute', 'click', etc.\n\n"
            response_text += f"Your message: \"{chat_req.message}\"\n\n"
            response_text += "Try asking me to:\n"
            response_text += "- Login to OpenEMIS as admin\n"
            response_text += "- Navigate to the students page\n"
            response_text += "- Click the add button\n"
            response_text += "- Fill the form with data"

            return ChatResponse(
                response=response_text,
                executed=False
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/history")
async def get_chat_history(
    user: User = Depends(require_authenticated),
    limit: int = 50
):
    """
    Get user's chat/automation history.

    Note: This is a placeholder for future implementation.
    Currently returns empty list as we're not tracking per-user history yet.

    Args:
        limit: Max number of history items to return

    Returns:
        List of chat history items
    """
    # TODO: Implement per-user history tracking
    return {"history": [], "message": "History tracking coming soon"}
