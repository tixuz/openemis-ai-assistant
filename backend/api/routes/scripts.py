"""
Script Management Routes - Reusable Automation Scripts API

Allows admins to create, edit, and manage reusable automation scripts.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import TypeAdapter

from backend.models.scripts import (
    AutomationScript,
    ScriptExecutionRequest,
    ScriptChainRequest,
    ScriptParameter
)
from backend.models.commands import Command
from backend.models.auth import User
from backend.models.history import ChatMessage
from backend.api.dependencies import require_admin, require_authenticated
from backend.core.script_store import get_script_store
from backend.core.automation_engine import execute_automation
from backend.core.variables_store import get_variables_store
from backend.core.history_store import get_history_store


router = APIRouter(prefix="/scripts", tags=["Scripts"])


@router.post("", status_code=201)
async def create_script(
    script: AutomationScript,
    user: User = Depends(require_admin)
):
    """
    Create a new reusable automation script.

    Requires: admin role

    Args:
        script: Script definition with commands and parameters

    Returns:
        Created script with ID
    """
    script_store = get_script_store()
    script.created_by = user.username

    try:
        script_id = await script_store.create_script(script)
        return {
            "id": script_id,
            "name": script.name,
            "message": f"Script '{script.name}' created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create script: {e}")


@router.get("")
async def list_scripts(
    user: User = Depends(require_authenticated),
    tags: Optional[str] = None
):
    """
    List all automation scripts.

    Args:
        tags: Comma-separated tags to filter by

    Returns:
        List of scripts (all users can view, only admins can edit)
    """
    script_store = get_script_store()

    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    scripts = await script_store.get_all_scripts(tags=tag_list)

    return {
        "scripts": [s.model_dump() for s in scripts],
        "total": len(scripts)
    }


@router.get("/{script_name}")
async def get_script(
    script_name: str,
    user: User = Depends(require_authenticated)
):
    """
    Get a specific script by name.

    Returns:
        Script details including commands and parameters
    """
    script_store = get_script_store()
    script = await script_store.get_script(script_name)

    if not script:
        raise HTTPException(status_code=404, detail=f"Script '{script_name}' not found")

    return script.model_dump()


@router.put("/{script_name}")
async def update_script(
    script_name: str,
    script: AutomationScript,
    user: User = Depends(require_admin)
):
    """
    Update an existing script.

    Requires: admin role

    Args:
        script_name: Current script name
        script: Updated script definition

    Returns:
        Success message
    """
    script_store = get_script_store()

    try:
        success = await script_store.update_script(script_name, script)
        if not success:
            raise HTTPException(status_code=404, detail=f"Script '{script_name}' not found")

        return {
            "message": f"Script '{script_name}' updated successfully",
            "new_name": script.name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update script: {e}")


@router.delete("/{script_name}")
async def delete_script(
    script_name: str,
    user: User = Depends(require_admin)
):
    """
    Delete a script.

    Requires: admin role

    Args:
        script_name: Name of script to delete

    Returns:
        Success message
    """
    script_store = get_script_store()
    success = await script_store.delete_script(script_name)

    if not success:
        raise HTTPException(status_code=404, detail=f"Script '{script_name}' not found")

    return {"message": f"Script '{script_name}' deleted successfully"}


@router.post("/execute")
async def execute_script(
    request: ScriptExecutionRequest,
    user: User = Depends(require_authenticated)
):
    """
    Execute a saved automation script.

    Available to all authenticated users.

    Args:
        request: Script name and parameter values

    Returns:
        Execution result with screenshots
    """
    script_store = get_script_store()
    variables_store = get_variables_store()

    # Get script
    script = await script_store.get_script(request.script_name)
    if not script:
        raise HTTPException(status_code=404, detail=f"Script '{request.script_name}' not found")

    # Validate parameters
    required_params = [p.name for p in script.parameters if p.required]
    missing = [p for p in required_params if p not in request.parameters]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required parameters: {', '.join(missing)}"
        )

    # Expand nested scripts first
    expanded_commands = []
    for cmd in script.commands:
        # Check if this is a script reference (script-type parameter)
        if isinstance(cmd, dict) and cmd.get("type") == "script":
            # This is a script parameter placeholder - need to expand it
            script_param_name = cmd.get("value", "").strip("{}")

            if script_param_name in request.parameters:
                nested_script_name = request.parameters[script_param_name]

                # Fetch the nested script
                nested_script = await script_store.get_script(nested_script_name)
                if not nested_script:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Nested script '{nested_script_name}' not found for parameter '{script_param_name}'"
                    )

                # Collect nested parameters (parent.child naming)
                nested_params = {}
                for req_param_name, req_param_value in request.parameters.items():
                    if req_param_name.startswith(f"{script_param_name}."):
                        # Extract the nested parameter name (after the dot)
                        nested_key = req_param_name.split(".", 1)[1]
                        nested_params[nested_key] = req_param_value

                # Substitute nested parameters in nested script commands
                nested_commands_json = json.dumps(nested_script.commands)
                for nested_key, nested_value in nested_params.items():
                    nested_commands_json = nested_commands_json.replace(f"{{{nested_key}}}", nested_value)

                # Add expanded commands
                expanded_commands.extend(json.loads(nested_commands_json))
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing script parameter: {script_param_name}"
                )
        else:
            # Regular command, keep as-is
            expanded_commands.append(cmd)

    # Now substitute regular parameters in expanded commands
    commands_json = json.dumps(expanded_commands)

    # First substitute script parameters (non-script-type ones)
    for param_name, param_value in request.parameters.items():
        # Skip nested parameters (they were already handled)
        if "." not in param_name:
            commands_json = commands_json.replace(f"{{{param_name}}}", param_value)

    # Then substitute user variables
    user_variables = await variables_store.get_variables_dict(user.username)
    for var_key, var_value in user_variables.items():
        commands_json = commands_json.replace(f"{{{var_key}}}", var_value)

    # Parse commands
    commands_data = json.loads(commands_json)

    # Validate commands using TypeAdapter
    command_list_adapter = TypeAdapter(List[Command])
    commands = command_list_adapter.validate_python(commands_data)

    # Add screenshot command if requested
    if request.take_screenshot:
        from backend.models.commands import ScreenshotCommand
        commands.append(ScreenshotCommand(type="screenshot"))

    # Execute automation
    try:
        result = await execute_automation(commands, headless=True)

        # Increment execution count
        await script_store.increment_execution_count(request.script_name)

        # Format response
        response_text = f"✅ Script '{request.script_name}' executed successfully!\n\n"
        response_text += f"**Commands executed:** {result.commands_executed}\n"
        response_text += f"**Time:** {result.execution_time_ms}ms\n\n"

        if result.screenshots:
            response_text += f"📸 **Screenshot captured**\n"

        # Save to scripts history branch
        history_store = get_history_store()
        chat_message = ChatMessage(
            username=user.username,
            message=f"Executed script: {request.script_name}",
            response=response_text,
            commands_generated=len(commands),
            executed=True,
            execution_result=result.to_dict()
        )
        await history_store.save_message(chat_message, branch="scripts")

        return {
            "success": True,
            "script_name": request.script_name,
            "response": response_text,
            "execution_result": result.to_dict()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Script execution failed: {str(e)}"
        )


@router.post("/chain")
async def execute_script_chain(
    request: ScriptChainRequest,
    user: User = Depends(require_authenticated)
):
    """
    Execute multiple scripts in sequence (e.g., login → navigate → action).

    This solves the "virgin with amnesia" problem - scripts can build on each other.

    Args:
        request: List of scripts to execute in order

    Returns:
        Combined execution results
    """
    # TODO: Implement session persistence for chained execution
    # For now, execute scripts sequentially without session reuse
    raise HTTPException(
        status_code=501,
        detail="Script chaining not yet implemented - coming soon!"
    )
