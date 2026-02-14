"""
Variables Routes - User Variables Management

Allows users to save and manage reusable variables like credentials, selectors, etc.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from backend.models.variables import (
    UserVariable, VariableCreate, VariableResponse, VariablesListResponse
)
from backend.models.auth import User
from backend.api.dependencies import require_authenticated
from backend.core.variables_store import get_variables_store


router = APIRouter(prefix="/user/variables", tags=["Variables"])


@router.get("", response_model=VariablesListResponse)
async def list_variables(
    user: User = Depends(require_authenticated)
):
    """
    Get all variables for the current user.

    Returns variables with passwords masked.
    """
    variables_store = get_variables_store()
    variables = await variables_store.get_all_variables(user.username)

    # Convert to responses with masked passwords
    responses = [
        VariableResponse.from_variable(var, mask_password=True)
        for var in variables
    ]

    return VariablesListResponse(
        variables=responses,
        total=len(responses)
    )


@router.post("", response_model=VariableResponse, status_code=201)
async def create_variable(
    variable: VariableCreate,
    user: User = Depends(require_authenticated)
):
    """
    Create or update a variable.

    If a variable with the same key exists, it will be updated.
    """
    variables_store = get_variables_store()

    var = await variables_store.set_variable(
        username=user.username,
        key=variable.key,
        value=variable.value,
        description=variable.description,
        var_type=variable.type
    )

    return VariableResponse.from_variable(var, mask_password=True)


@router.get("/{key}", response_model=VariableResponse)
async def get_variable(
    key: str,
    user: User = Depends(require_authenticated),
    reveal: bool = False
):
    """
    Get a specific variable by key.

    Args:
        key: Variable key
        reveal: If true, show actual password value (for admin use)
    """
    variables_store = get_variables_store()
    var = await variables_store.get_variable(user.username, key)

    if not var:
        raise HTTPException(status_code=404, detail=f"Variable '{key}' not found")

    return VariableResponse.from_variable(var, mask_password=not reveal)


@router.delete("/{key}")
async def delete_variable(
    key: str,
    user: User = Depends(require_authenticated)
):
    """
    Delete a variable.
    """
    variables_store = get_variables_store()
    success = await variables_store.delete_variable(user.username, key)

    if not success:
        raise HTTPException(status_code=404, detail=f"Variable '{key}' not found")

    return {"message": f"Variable '{key}' deleted successfully"}


@router.get("/substitute/preview")
async def preview_substitution(
    text: str,
    user: User = Depends(require_authenticated)
):
    """
    Preview variable substitution in text.

    Useful for testing how variables will be replaced.

    Example: text="Login with {username}" -> "Login with admin"
    """
    variables_store = get_variables_store()
    result = await variables_store.substitute_variables(user.username, text)

    return {
        "original": text,
        "substituted": result
    }
