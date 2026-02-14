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
from backend.api.dependencies import require_admin, require_authenticated
from backend.core.script_store import get_script_store
from backend.core.automation_engine import execute_automation
from backend.core.variables_store import get_variables_store


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

    # Substitute parameters in commands
    commands_json = json.dumps(script.commands)

    # First substitute script parameters
    for param_name, param_value in request.parameters.items():
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
