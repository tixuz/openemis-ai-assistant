"""
Workflow Engine - Intent Recognition and Execution

Converts natural language like "mark attendance, john is absent"
into structured workflows that execute script chains.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from backend.models.workflows import (
    WorkflowIntent,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    INTENT_PATTERNS,
    DEFAULT_WORKFLOWS
)
from backend.core.script_store import get_script_store
from backend.core.automation_engine import execute_automation
from backend.models.commands import Command
from pydantic import TypeAdapter


class IntentDetector:
    """Detects user intent from natural language"""

    def __init__(self):
        self.patterns = INTENT_PATTERNS

    async def detect_intent(self, message: str) -> Optional[WorkflowIntent]:
        """
        Detect intent from user message.

        Args:
            message: User's natural language message

        Returns:
            WorkflowIntent if detected, None otherwise
        """
        message_lower = message.lower()

        # Check each intent pattern
        for intent_type, pattern in self.patterns.items():
            # Count keyword matches
            keyword_matches = sum(1 for kw in pattern["keywords"] if kw in message_lower)

            if keyword_matches >= 2:  # At least 2 keywords match
                # Extract entities
                entities = self._extract_entities(message, pattern["entities"])

                return WorkflowIntent(
                    intent_type=intent_type,
                    entities=entities,
                    confidence=min(1.0, keyword_matches / len(pattern["keywords"])),
                    original_message=message
                )

        return None

    def _extract_entities(self, message: str, entity_types: List[str]) -> Dict[str, Any]:
        """
        Extract entities from message.

        Args:
            message: User message
            entity_types: Types of entities to extract

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Extract students (names)
        if "students" in entity_types:
            students = self._extract_student_names(message)
            if students:
                entities["students"] = students

        # Extract date
        if "date" in entity_types:
            date = self._extract_date(message)
            entities["date"] = date

        # Extract status (present/absent)
        if "status" in entity_types:
            status = self._extract_status(message)
            if status:
                entities["status"] = status

        # Extract institution code
        if "institution_code" in entity_types:
            code = self._extract_institution_code(message)
            if code:
                entities["institution_code"] = code

        return entities

    def _extract_student_names(self, message: str) -> List[str]:
        """Extract student names from message"""
        # Pattern: "john", "john and jack", "john, jack, and mary"
        names = []

        # Common name pattern (capitalized words)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(name_pattern, message)

        # Filter out common words
        stopwords = {'Mark', 'Check', 'Show', 'View', 'Export', 'Today', 'Missing', 'Absent', 'Present'}
        names = [name for name in matches if name not in stopwords]

        # Also check for lowercase names after "absent", "missing", "present"
        patterns = [
            r'(?:absent|missing|present):\s*([a-z\s,and]+)',
            r'([a-z\s,and]+)\s+(?:is|are)\s+(?:absent|missing|present)',
        ]

        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                names_text = match.group(1)
                # Split by "and" or ","
                additional_names = re.split(r'\s+and\s+|,\s*', names_text)
                names.extend([name.strip().title() for name in additional_names if name.strip()])

        return list(set(names))  # Remove duplicates

    def _extract_date(self, message: str) -> str:
        """Extract date from message"""
        message_lower = message.lower()

        # Check for relative dates
        if "today" in message_lower:
            return datetime.now().strftime("%Y-%m-%d")
        elif "yesterday" in message_lower:
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(days=1)
            return yesterday.strftime("%Y-%m-%d")
        elif "tomorrow" in message_lower:
            from datetime import timedelta
            tomorrow = datetime.now() + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d")

        # Check for specific date format (YYYY-MM-DD, DD/MM/YYYY, etc.)
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2026-02-14
            r'(\d{2}/\d{2}/\d{4})',  # 14/02/2026
        ]

        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)

        # Default to today
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_status(self, message: str) -> Optional[str]:
        """Extract attendance status from message"""
        message_lower = message.lower()

        if "absent" in message_lower or "missing" in message_lower:
            return "absent"
        elif "present" in message_lower:
            return "present"

        # Default to absent if students are mentioned without status
        return "absent"

    def _extract_institution_code(self, message: str) -> Optional[str]:
        """Extract institution code from message"""
        # Pattern: P1002, P-1002, etc.
        pattern = r'\b([A-Z]\d{4}|[A-Z]-?\d{4})\b'
        match = re.search(pattern, message)

        if match:
            return match.group(1)

        return None


class WorkflowStore:
    """Store and retrieve workflow definitions"""

    def __init__(self, file_path: str = "data/workflows/workflows.jsonl"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._load_cache()

    def _load_cache(self):
        """Load workflows from file or use defaults"""
        if self.file_path.exists():
            with open(self.file_path, "r") as f:
                for line in f:
                    if line.strip():
                        wf = WorkflowDefinition(**json.loads(line))
                        self._workflows[wf.intent_type] = wf
        else:
            # Load defaults
            for wf_data in DEFAULT_WORKFLOWS:
                wf = WorkflowDefinition(**wf_data)
                self._workflows[wf.intent_type] = wf
            self._save_to_disk()

    def _save_to_disk(self):
        """Save all workflows to disk"""
        with open(self.file_path, "w") as f:
            for wf in self._workflows.values():
                f.write(json.dumps(wf.model_dump()) + "\n")

    async def get_workflow(self, intent_type: str) -> Optional[WorkflowDefinition]:
        """Get workflow for intent type"""
        return self._workflows.get(intent_type)

    async def get_all_workflows(self) -> List[WorkflowDefinition]:
        """Get all workflows"""
        return list(self._workflows.values())


class WorkflowEngine:
    """Executes workflows by running script chains"""

    def __init__(self):
        self.intent_detector = IntentDetector()
        self.workflow_store = WorkflowStore()

    async def execute_from_message(
        self,
        message: str,
        user,
        variables_store
    ) -> Tuple[bool, Optional[WorkflowExecution]]:
        """
        Detect intent and execute workflow if found.

        Args:
            message: User's natural language message
            user: User object
            variables_store: Variable store for substitution

        Returns:
            (workflow_found, execution_result)
        """
        # Detect intent
        intent = await self.intent_detector.detect_intent(message)
        if not intent:
            return (False, None)

        # Get workflow definition
        workflow = await self.workflow_store.get_workflow(intent.intent_type)
        if not workflow:
            return (False, None)

        # Check required entities
        missing = [e for e in workflow.requires_entities if e not in intent.entities]
        if missing:
            # Could ask user for missing info, but for now just fail
            execution = WorkflowExecution(
                workflow_id=workflow.id,
                intent=intent,
                total_steps=len(workflow.steps),
                success=False,
                message=f"❌ Missing required information: {', '.join(missing)}. Please specify."
            )
            return (True, execution)

        # Execute workflow
        execution = await self._execute_workflow(workflow, intent, user, variables_store)
        return (True, execution)

    async def _execute_workflow(
        self,
        workflow: WorkflowDefinition,
        intent: WorkflowIntent,
        user,
        variables_store
    ) -> WorkflowExecution:
        """Execute workflow steps"""
        start_time = datetime.now()
        script_store = get_script_store()
        user_variables = await variables_store.get_variables_dict(user.username)

        all_commands = []
        steps_executed = 0
        screenshots = []

        try:
            # Execute each step
            for step in workflow.steps:
                # Get script
                script = await script_store.get_script(step.script_name)
                if not script:
                    raise Exception(f"Script '{step.script_name}' not found")

                # Substitute parameters
                commands_json = json.dumps(script.commands)

                # Substitute workflow parameters from entities
                for param_name, param_value in step.parameters.items():
                    # Check if parameter references an entity {entity_name}
                    if param_value.startswith("{") and param_value.endswith("}"):
                        entity_key = param_value[1:-1]  # Remove {}
                        if entity_key in intent.entities:
                            entity_value = intent.entities[entity_key]
                            # If entity is a list, join with commas
                            if isinstance(entity_value, list):
                                entity_value = ", ".join(entity_value)
                            commands_json = commands_json.replace(param_value, str(entity_value))

                # Substitute user variables
                for var_key, var_value in user_variables.items():
                    commands_json = commands_json.replace(f"{{{var_key}}}", var_value)

                # Parse commands
                commands_data = json.loads(commands_json)
                command_list_adapter = TypeAdapter(List[Command])
                commands = command_list_adapter.validate_python(commands_data)

                all_commands.extend(commands)
                steps_executed += 1

            # Execute all commands
            result = await execute_automation(all_commands, headless=True)

            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Format success message with entity substitution
            message = workflow.success_message
            for entity_key, entity_value in intent.entities.items():
                if isinstance(entity_value, list):
                    entity_value = ", ".join(entity_value)
                message = message.replace(f"{{{entity_key}}}", str(entity_value))

            return WorkflowExecution(
                workflow_id=workflow.id,
                intent=intent,
                steps_executed=steps_executed,
                total_steps=len(workflow.steps),
                success=result.success,
                message=message if result.success else workflow.error_message,
                execution_time_ms=execution_time_ms,
                screenshot_data=result.screenshot_data
            )

        except Exception as e:
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return WorkflowExecution(
                workflow_id=workflow.id,
                intent=intent,
                steps_executed=steps_executed,
                total_steps=len(workflow.steps),
                success=False,
                message=f"{workflow.error_message} (Error: {str(e)})",
                execution_time_ms=execution_time_ms
            )


# Singleton instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
