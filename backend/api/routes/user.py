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
from backend.core.script_store import get_script_store
from backend.core.workflow_engine import get_workflow_engine
from backend.models.learning import LearningExample
from backend.models.scripts import AutomationScript
from backend.models.commands import Command
from backend.config import settings
import re
import json
from pydantic import TypeAdapter
from typing import List


router = APIRouter(prefix="/user", tags=["User"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


async def detect_and_execute_script(
    message: str,
    user: User,
    variables_store
) -> tuple[bool, List[Command], str]:
    """
    Detect if message contains "run {script_name}" and execute it.

    Returns:
        (found_script, commands, script_name)
    """
    # Pattern: "run <script_name> script" or "execute <script_name>"
    patterns = [
        r'run\s+(?:the\s+)?(\w+)\s+script',
        r'execute\s+(?:the\s+)?(\w+)\s+script',
        r'run\s+(\w+)',
        r'execute\s+(\w+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            script_name = match.group(1)

            # Try to find the script
            script_store = get_script_store()
            script = await script_store.get_script(script_name)

            if script:
                # Load user variables
                user_variables = await variables_store.get_variables_dict(user.username)

                # Substitute parameters in commands
                commands_json = json.dumps(script.commands)

                # Substitute user variables (if script uses {my_username}, etc.)
                for var_key, var_value in user_variables.items():
                    commands_json = commands_json.replace(f"{{{var_key}}}", var_value)

                # Parse commands
                commands_data = json.loads(commands_json)
                command_list_adapter = TypeAdapter(List[Command])
                commands = command_list_adapter.validate_python(commands_data)

                return (True, commands, script.name)

    return (False, [], "")


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

    try:
        # Get dependencies
        llm_client = LLMClient(server_url=settings.LLM_SERVER_URL)
        learning_store = get_learning_store()
        prompt_manager = get_prompt_manager()
        variables_store = get_variables_store()
        script_store = get_script_store()
        workflow_engine = get_workflow_engine()

        # Load user variables
        user_variables = await variables_store.get_variables_dict(user.username)

        # TRY 1: Check if this matches a workflow intent (e.g., "mark attendance, john is absent")
        workflow_found, workflow_execution = await workflow_engine.execute_from_message(
            chat_req.message,
            user,
            variables_store
        )

        if workflow_found and workflow_execution:
            # Workflow executed! Return natural language response
            history_store = get_history_store()
            chat_message = ChatMessage(
                username=user.username,
                message=chat_req.message,
                response=workflow_execution.message,
                commands_generated=workflow_execution.steps_executed,
                executed=True,
                execution_result={
                    "success": workflow_execution.success,
                    "workflow_id": workflow_execution.workflow_id,
                    "intent": workflow_execution.intent.model_dump(),
                    "steps_executed": workflow_execution.steps_executed,
                    "screenshot_data": workflow_execution.screenshot_data
                }
            )
            await history_store.save_message(chat_message)

            return ChatResponse(
                response=workflow_execution.message,
                commands_generated=workflow_execution.steps_executed,
                executed=True,
                execution_result={
                    "success": workflow_execution.success,
                    "screenshot_data": workflow_execution.screenshot_data
                }
            )

        # TRY 2: Check if user wants to run a saved script
        found_script, script_commands, script_name = await detect_and_execute_script(
            chat_req.message,
            user,
            variables_store
        )

        # Determine if this needs additional LLM-generated commands
        # Pattern: "run login, then navigate to X"
        has_additional_actions = found_script and ("then" in message or "and then" in message)

        # Initialize commands list
        all_commands = []

        # Start with script commands if found
        if found_script:
            all_commands.extend(script_commands)

        # Find similar examples
        similar_examples = await learning_store.find_similar(chat_req.message, limit=3)

        # Build prompt with variables and scripts information
        system_prompt = prompt_manager.build_enhanced_prompt(similar_examples)

        # Add variables info to prompt if user has any
        if user_variables:
            variables_info = "\n\n## User Variables Available:\n"
            variables_info += "You can use these variables in commands by referencing {variable_name}:\n"
            for key in user_variables.keys():
                variables_info += f"- {{{key}}}\n"
            system_prompt += variables_info

        # Add available scripts to prompt
        all_scripts = await script_store.get_all_scripts()
        if all_scripts:
            scripts_info = "\n\n## Available Saved Scripts:\n"
            scripts_info += "User can reference these scripts by saying 'run {script_name}':\n"
            for script in all_scripts:
                scripts_info += f"- **{script.name}**: {script.description}\n"
            system_prompt += scripts_info

        # Determine if we need to generate additional commands
        needs_llm_generation = (not found_script) or has_additional_actions

        if needs_llm_generation:
            # If chaining with script, extract the "then X" part for LLM
            llm_intent = chat_req.message
            if has_additional_actions:
                # Extract text after "then" for LLM to generate commands
                match = re.search(r'then\s+(.+)', message, re.IGNORECASE)
                if match:
                    llm_intent = match.group(1)

            # Generate commands from LLM
            generated_commands = await llm_client.generate_commands(
                user_intent=llm_intent,
                system_prompt=system_prompt,
                examples=[ex.model_dump() for ex in similar_examples]
            )

            # Substitute variables in generated commands
            if user_variables:
                for cmd in generated_commands:
                    for field_name, field_value in cmd.model_dump().items():
                        if isinstance(field_value, str):
                            for var_key, var_value in user_variables.items():
                                field_value = field_value.replace(f"{{{var_key}}}", var_value)
                            setattr(cmd, field_name, field_value)

            # Add generated commands to the list
            all_commands.extend(generated_commands)

        # Execute all commands (script + generated)
        if all_commands:
            result = await execute_automation(all_commands, headless=True)

            # Save successful execution
            if result.success:
                example = LearningExample(
                    task_description=chat_req.message,
                    user_intent=chat_req.message,
                    commands=[cmd.model_dump() for cmd in all_commands],
                    success=True,
                    context=chat_req.context or {},
                    execution_time_ms=result.execution_time_ms
                )
                await learning_store.save_example(example)

                # Increment script execution count if used
                if found_script:
                    await script_store.increment_execution_count(script_name)

            # Format response with command details
            if result.success:
                response_text = f"✅ Automation completed successfully!\n\n"

                # Indicate if script was used
                if found_script:
                    response_text += f"🔧 **Used script:** `{script_name}`\n"
                    if has_additional_actions:
                        response_text += f"➕ **Plus additional actions** (generated by AI)\n"
                    response_text += "\n"

                response_text += f"**Commands executed:** {result.commands_executed}\n"
                response_text += f"**Time:** {result.execution_time_ms}ms\n\n"

                # Show what was done
                response_text += "**Actions taken:**\n"
                for i, cmd in enumerate(all_commands, 1):
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
                commands_generated=len(all_commands),
                executed=True,
                execution_result=result.to_dict()
            )
            await history_store.save_message(chat_message)

            return ChatResponse(
                response=response_text,
                commands_generated=len(all_commands),
                executed=True,
                execution_result=result.to_dict()
            )
        else:
            # No commands to execute - provide helpful info
            response_text = "I'm an automation assistant for OpenEMIS.\n\n"

            # If they mentioned a script that doesn't exist
            if "run" in message or "execute" in message:
                response_text += "💡 **Available scripts:**\n"
                if all_scripts:
                    for script in all_scripts:
                        response_text += f"- `{script.name}`: {script.description}\n"
                    response_text += "\n**Usage:** Say 'run {script_name}' to execute a script\n"
                    response_text += "**Example:** 'run login then navigate to institutions'\n\n"
                else:
                    response_text += "No scripts available yet. Admins can create scripts at /admin/scripts\n\n"

            # General help
            response_text += "To execute automation, use action words like:\n"
            response_text += "- 'run {script_name}' - Execute a saved script\n"
            response_text += "- 'navigate to...', 'click...', 'fill...'\n"
            response_text += "- 'login to OpenEMIS as admin'\n"

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
    offset: int = 0,
    load_screenshots: bool = False
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
        load_screenshots: Whether to load screenshot base64 data (default: False)
                         Screenshots are stored separately to avoid bloating history.
                         Set to True to load full base64 data for display.

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

    # Optionally load screenshots
    if load_screenshots:
        for item in history_data:
            if item.get("execution_result") and item["execution_result"].get("screenshot_data"):
                screenshot_list = item["execution_result"]["screenshot_data"]
                for screenshot_info in screenshot_list:
                    if "filename" in screenshot_info and "data" not in screenshot_info:
                        # Load screenshot from file
                        filename = screenshot_info["filename"]
                        base64_data = await history_store.load_screenshot(
                            username=user.username,
                            filename=filename
                        )
                        if base64_data:
                            screenshot_info["data"] = base64_data

    return {
        "history": history_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }
