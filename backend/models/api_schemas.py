"""
API Request/Response Schemas

Pydantic models for API endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ChatRequest(BaseModel):
    """User chat request"""
    message: str = Field(..., min_length=1, max_length=5000)
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response with AI message"""
    response: str
    commands_generated: Optional[int] = None
    executed: bool = False
    execution_result: Optional[Dict[str, Any]] = None


class AutomationRequest(BaseModel):
    """Request to execute automation"""
    task_description: str = Field(..., min_length=1)
    auto_execute: bool = True
    context: Optional[Dict[str, Any]] = None


class AutomationResponse(BaseModel):
    """Automation execution response"""
    task_id: str
    commands: List[Dict[str, Any]]
    executed: bool
    result: Optional[Dict[str, Any]] = None


class PromptUpdate(BaseModel):
    """Update system prompt"""
    content: str = Field(..., min_length=10)
    description: Optional[str] = None


class PromptResponse(BaseModel):
    """System prompt data"""
    content: str
    updated_at: str


class ExampleListResponse(BaseModel):
    """List of learning examples"""
    examples: List[Dict[str, Any]]
    total: int


class AnalyticsResponse(BaseModel):
    """Analytics data"""
    total_executions: int
    success_rate: float
    avg_execution_time_ms: float
    total_examples: int
    recent_tasks: List[Dict[str, Any]]
