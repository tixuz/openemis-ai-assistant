"""
Intent-Based Workflow System - Natural Language to Automation

Maps user intents to script chains with entity extraction.
Enables natural language like "mark attendance, john is absent"
instead of technical "run login then navigate to attendance"
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class WorkflowIntent(BaseModel):
    """Recognized user intent with entities"""

    intent_type: str = Field(..., description="Intent type (e.g., MARK_ATTENDANCE, EXPORT_GRADES)")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    original_message: str = Field(..., description="Original user message")


class WorkflowStep(BaseModel):
    """Single step in a workflow"""

    script_name: str = Field(..., description="Script to execute")
    parameters: Dict[str, str] = Field(default_factory=dict, description="Parameters for script")
    description: str = Field(..., description="Human-readable description")
    optional: bool = Field(False, description="Can skip if fails")


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent_type: str = Field(..., description="Intent this workflow handles")
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="What this workflow does")
    steps: List[WorkflowStep] = Field(..., description="Steps to execute")
    success_message: str = Field(..., description="Message to show on success")
    error_message: str = Field(..., description="Message to show on error")
    requires_entities: List[str] = Field(default_factory=list, description="Required entities")
    examples: List[str] = Field(default_factory=list, description="Example phrases")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wf-001",
                "intent_type": "MARK_ATTENDANCE",
                "name": "Mark Student Attendance",
                "description": "Mark students as present or absent for today",
                "steps": [
                    {
                        "script_name": "login",
                        "parameters": {},
                        "description": "Login to OpenEMIS"
                    },
                    {
                        "script_name": "navigate_to_attendance",
                        "parameters": {"date": "{date}"},
                        "description": "Navigate to attendance page"
                    },
                    {
                        "script_name": "mark_students_absent",
                        "parameters": {"students": "{absent_students}"},
                        "description": "Mark students as absent"
                    }
                ],
                "success_message": "✅ Attendance marked. {absent_students} marked absent for {date}. Refresh the page to see.",
                "error_message": "❌ Failed to mark attendance. Please try again or mark manually.",
                "requires_entities": ["absent_students", "date"],
                "examples": [
                    "mark today's attendance, john and jack are absent",
                    "mark attendance, john missing",
                    "john and jack are absent today"
                ]
            }
        }


class WorkflowExecution(BaseModel):
    """Result of workflow execution"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = Field(..., description="Workflow that was executed")
    intent: WorkflowIntent = Field(..., description="Recognized intent")
    steps_executed: int = Field(0, description="Number of steps completed")
    total_steps: int = Field(..., description="Total number of steps")
    success: bool = Field(False, description="Whether workflow succeeded")
    message: str = Field(..., description="User-friendly result message")
    execution_time_ms: int = Field(0, description="Total execution time")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    screenshot_data: List[Dict[str, str]] = Field(default_factory=list, description="Screenshots if any")


# Pre-defined workflow intents
INTENT_PATTERNS = {
    "MARK_ATTENDANCE": {
        "keywords": ["mark", "attendance", "absent", "missing", "present"],
        "entities": ["students", "date", "status"],
        "examples": [
            "mark attendance, john is absent",
            "john and jack are missing today",
            "mark today's attendance"
        ]
    },
    "CHECK_HOMEWORK": {
        "keywords": ["check", "homework", "assignments", "submitted"],
        "entities": ["students", "subject", "date"],
        "examples": [
            "check who submitted math homework",
            "show homework status for john"
        ]
    },
    "EXPORT_GRADES": {
        "keywords": ["export", "grades", "marks", "download", "csv"],
        "entities": ["class", "subject", "period"],
        "examples": [
            "export grades for class 5A",
            "download math grades as csv"
        ]
    },
    "VIEW_STUDENT_INFO": {
        "keywords": ["show", "view", "display", "student", "info", "profile"],
        "entities": ["student_name"],
        "examples": [
            "show john's profile",
            "view student john smith"
        ]
    },
    "SEARCH_INSTITUTION": {
        "keywords": ["search", "find", "institution", "school", "code"],
        "entities": ["institution_code", "institution_name"],
        "examples": [
            "search for institution P1002",
            "find school by code P1002"
        ]
    }
}


# Default workflow definitions
DEFAULT_WORKFLOWS = [
    {
        "intent_type": "MARK_ATTENDANCE",
        "name": "Mark Student Attendance",
        "description": "Mark students as present or absent",
        "steps": [
            {
                "script_name": "login",
                "parameters": {},
                "description": "Login to system"
            },
            {
                "script_name": "navigate_to_attendance",
                "parameters": {"date": "{date}"},
                "description": "Open attendance page"
            },
            {
                "script_name": "mark_students",
                "parameters": {
                    "students": "{students}",
                    "status": "{status}"
                },
                "description": "Mark student attendance"
            }
        ],
        "success_message": "✅ Attendance marked. {students} marked {status} for {date}. Refresh the page to see changes.",
        "error_message": "❌ Could not mark attendance. Please check if students exist and try again.",
        "requires_entities": ["students", "status"],
        "examples": [
            "mark attendance, john and jack are absent",
            "john is missing today",
            "mark john and sarah present"
        ]
    },
    {
        "intent_type": "SEARCH_INSTITUTION",
        "name": "Search Institution",
        "description": "Find and navigate to institution by code or name",
        "steps": [
            {
                "script_name": "login",
                "parameters": {},
                "description": "Login to system"
            },
            {
                "script_name": "navigate_to_institutions",
                "parameters": {},
                "description": "Open institutions page"
            },
            {
                "script_name": "search_institution",
                "parameters": {"code": "{institution_code}"},
                "description": "Search for institution"
            }
        ],
        "success_message": "✅ Found institution {institution_code}. Displaying details.",
        "error_message": "❌ Institution not found. Please check the code and try again.",
        "requires_entities": ["institution_code"],
        "examples": [
            "go to institution P1002",
            "search for school P1002",
            "open institution P1002"
        ]
    }
]
