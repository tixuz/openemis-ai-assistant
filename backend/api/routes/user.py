"""
User Routes - Chat Interface for End Users

Provides simple chat interface for teachers and OpenEMIS users.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.models.api_schemas import ChatRequest, ChatResponse
from backend.models.auth import User
from backend.models.history import ChatMessage
from backend.api.dependencies import require_authenticated
from backend.core.automation_engine import execute_automation
from backend.core.llm_client import LLMClient
from backend.core.learning_store import get_learning_store
from backend.core.history_store import get_history_store
from backend.core.variables_store import get_variables_store
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
        variables_store = get_variables_store()

        # Load user variables
        user_variables = await variables_store.get_variables_dict(user.username)

        # Find similar examples
        similar_examples = await learning_store.find_similar(chat_req.message, limit=3)

        # Build prompt with variables information
        system_prompt = prompt_manager.build_enhanced_prompt(similar_examples)

        # Add variables info to prompt if user has any
        if user_variables:
            variables_info = "\n\n## User Variables Available:\n"
            variables_info += "You can use these variables in commands by referencing {variable_name}:\n"
            for key in user_variables.keys():
                variables_info += f"- {{{key}}}\n"
            system_prompt += variables_info

        if is_action:
            # Generate and execute automation
            commands = await llm_client.generate_commands(
                user_intent=chat_req.message,
                system_prompt=system_prompt,
                examples=[ex.model_dump() for ex in similar_examples]
            )

            # Substitute variables in commands
            if user_variables:
                for cmd in commands:
                    # Substitute in all string fields
                    for field_name, field_value in cmd.model_dump().items():
                        if isinstance(field_value, str):
                            # Replace {variable} with actual value
                            for var_key, var_value in user_variables.items():
                                field_value = field_value.replace(f"{{{var_key}}}", var_value)
                            # Update the field
                            setattr(cmd, field_name, field_value)

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

            # Format response with command details
            if result.success:
                response_text = f"✅ Automation completed successfully!\n\n"
                response_text += f"**Commands executed:** {result.commands_executed}\n"
                response_text += f"**Time:** {result.execution_time_ms}ms\n\n"

                # Show what was done
                response_text += "**Actions taken:**\n"
                for i, cmd in enumerate(commands, 1):
                    if cmd.type == "navigate":
                        response_text += f"{i}. 🌐 Navigated to: {cmd.url}\n"
                    elif cmd.type == "click":
                        response_text += f"{i}. 👆 Clicked: {cmd.selector}\n"
                    elif cmd.type == "fill":
                        response_text += f"{i}. ✏️ Filled: {cmd.selector} = '{cmd.value}'\n"
                    elif cmd.type == "wait_for_navigation":
                        response_text += f"{i}. ⏳ Waited for page load\n"
                    elif cmd.type == "screenshot":
                        response_text += f"{i}. 📸 Took screenshot\n"
                    else:
                        response_text += f"{i}. {cmd.type}\n"

                # Show screenshots count (actual images will be displayed by frontend)
                if result.screenshots:
                    response_text += f"\n**Screenshots:** {len(result.screenshots)} captured (displayed below)\n"

                # Show extracted data if any
                if result.extracted_data:
                    response_text += f"\n**Extracted data:**\n"
                    for key, value in result.extracted_data.items():
                        response_text += f"- {key}: {value}\n"
            else:
                response_text = f"❌ Automation failed: {result.error}"

            # Save to conversation history
            history_store = get_history_store()
            chat_message = ChatMessage(
                username=user.username,
                message=chat_req.message,
                response=response_text,
                commands_generated=len(commands),
                executed=True,
                execution_result=result.to_dict()
            )
            await history_store.save_message(chat_message)

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

            # Save to conversation history
            history_store = get_history_store()
            chat_message = ChatMessage(
                username=user.username,
                message=chat_req.message,
                response=response_text,
                executed=False
            )
            await history_store.save_message(chat_message)

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
    limit: int = 50,
    offset: int = 0
):
    """
    Get user's chat/automation history.

    Returns conversation history including:
    - User messages
    - AI responses
    - Automation results (if any)
    - Timestamps

    Args:
        limit: Max number of history items to return (default: 50)
        offset: Number of items to skip for pagination (default: 0)

    Returns:
        Dictionary with history list and total count
    """
    history_store = get_history_store()

    # Get user's history
    messages = await history_store.get_user_history(
        username=user.username,
        limit=limit,
        offset=offset
    )

    # Get total count
    total = await history_store.count_user_messages(user.username)

    # Convert to dict
    history_data = [msg.model_dump() for msg in messages]

    return {
        "history": history_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }
