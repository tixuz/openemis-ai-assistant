"""
Workflow Engine - Enhanced with Code Analyzer Integration

Converts natural language to workflows with REAL selectors from OpenEMIS source code.
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

# Import CodeAnalyzer
try:
    from backend.core.code_analyzer import get_code_analyzer
    CODE_ANALYZER_AVAILABLE = True
except ImportError:
    CODE_ANALYZER_AVAILABLE = False
    print("⚠️  CodeAnalyzer not available - selectors won't be enriched")


class IntentDetector:
    """Detects user intent from natural language"""

    def __init__(self):
        self.patterns = INTENT_PATTERNS
        
        # Load smart templates if available
        self.smart_templates = self._load_smart_templates()

    def _load_smart_templates(self) -> Dict:
        """Load smart templates with pre-defined intents."""
        template_file = Path("data/smart_templates.json")
        if template_file.exists():
            try:
                with open(template_file) as f:
                    data = json.load(f)
                    return data.get("templates", {})
            except Exception as e:
                print(f"⚠️  Could not load smart templates: {e}")
        return {}

    async def detect_intent(self, message: str) -> Optional[WorkflowIntent]:
        """
        Detect intent from user message.
        Now checks smart templates first for better matching.
        """
        message_lower = message.lower()

        # 1. Check smart templates first (more specific)
        for template_id, template in self.smart_templates.items():
            # Check trigger keywords
            keyword_matches = sum(1 for kw in template.get("trigger_keywords", []) 
                                if kw in message_lower)
            
            if keyword_matches >= 2:  # At least 2 keywords match
                # Extract entities based on template
                entities = self._extract_entities_from_template(message, template)
                
                return WorkflowIntent(
                    intent_type=template["intent"],
                    entities=entities,
                    confidence=template.get("confidence", 0.85),
                    original_message=message
                )

        # 2. Fallback to original pattern matching
        for intent_type, pattern in self.patterns.items():
            keyword_matches = sum(1 for kw in pattern["keywords"] if kw in message_lower)

            if keyword_matches >= 2:
                entities = self._extract_entities(message, pattern["entities"])

                return WorkflowIntent(
                    intent_type=intent_type,
                    entities=entities,
                    confidence=min(1.0, keyword_matches / len(pattern["keywords"])),
                    original_message=message
                )

        return None

    def _extract_entities_from_template(self, message: str, template: dict) -> Dict[str, Any]:
        """Extract entities based on template's entity extraction rules."""
        entities = {}
        
        # Get extraction rules from template
        extraction_rules = template.get("entity_extraction", {})
        
        # Use standard extraction as baseline
        for var_name, var_config in template.get("variables", {}).items():
            var_type = var_config.get("type")
            
            if var_type == "array":
                # Extract list (e.g., student names)
                if var_name == "students":
                    students = self._extract_student_names(message)
                    if students:
                        entities["students"] = students
            
            elif var_type == "date":
                entities["date"] = self._extract_date(message)
            
            elif var_type == "enum":
                # Extract enum value (e.g., status)
                if var_name == "status":
                    status = self._extract_status(message)
                    if status:
                        entities["status"] = status
            
            elif var_type == "string":
                # Extract string based on pattern
                if var_name == "institution_code":
                    code = self._extract_institution_code(message)
                    if code:
                        entities["institution_code"] = code
                elif var_name == "student_name":
                    students = self._extract_student_names(message)
                    if students:
                        entities["student_name"] = students[0]
        
        return entities

    def _extract_entities(self, message: str, entity_types: List[str]) -> Dict[str, Any]:
        """Extract entities from message."""
        entities = {}

        if "students" in entity_types:
            students = self._extract_student_names(message)
            if students:
                entities["students"] = students

        if "date" in entity_types:
            date = self._extract_date(message)
            entities["date"] = date

        if "status" in entity_types:
            status = self._extract_status(message)
            if status:
                entities["status"] = status

        if "institution_code" in entity_types:
            code = self._extract_institution_code(message)
            if code:
                entities["institution_code"] = code

        return entities

    def _extract_student_names(self, message: str) -> List[str]:
        """Extract student names from message"""
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
                additional_names = re.split(r'\s+and\s+|,\s*', names_text)
                names.extend([name.strip().title() for name in additional_names if name.strip()])

        return list(set(names))

    def _extract_date(self, message: str) -> str:
        """Extract date from message"""
        message_lower = message.lower()

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

        # Check for specific date format
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)

        return datetime.now().strftime("%Y-%m-%d")

    def _extract_status(self, message: str) -> Optional[str]:
        """Extract attendance status from message"""
        message_lower = message.lower()

        if "absent" in message_lower or "missing" in message_lower:
            return "absent"
        elif "present" in message_lower:
            return "present"

        return "absent"

    def _extract_institution_code(self, message: str) -> Optional[str]:
        """Extract institution code from message"""
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
    """Executes workflows with real selector enrichment"""

    def __init__(self):
        self.intent_detector = IntentDetector()
        self.workflow_store = WorkflowStore()
        
        # Initialize code analyzer if available
        if CODE_ANALYZER_AVAILABLE:
            try:
                self.code_analyzer = get_code_analyzer()
                print("✓ CodeAnalyzer initialized for selector enrichment")
            except Exception as e:
                self.code_analyzer = None
                print(f"⚠️  CodeAnalyzer initialization failed: {e}")
        else:
            self.code_analyzer = None

    async def execute_from_message(
        self,
        message: str,
        user,
        variables_store
    ) -> Tuple[bool, Optional[WorkflowExecution]]:
        """
        Detect intent and execute workflow with selector enrichment.
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
        """Execute workflow steps with selector enrichment"""
        start_time = datetime.now()
        script_store = get_script_store()
        user_variables = await variables_store.get_variables_dict(user.username)

        # Get selector context if code analyzer available
        selector_context = {}
        if self.code_analyzer:
            try:
                selectors = self.code_analyzer.find_selectors_for_task(
                    intent.original_message
                )
                selector_context = selectors
                print(f"✓ Enriched with {len(selectors.get('ids', []))} IDs, "
                      f"{len(selectors.get('names', []))} names from source code")
            except Exception as e:
                print(f"⚠️  Selector enrichment failed: {e}")

        all_commands = []
        steps_executed = 0

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
                    if param_value.startswith("{") and param_value.endswith("}"):
                        entity_key = param_value[1:-1]
                        if entity_key in intent.entities:
                            entity_value = intent.entities[entity_key]
                            if isinstance(entity_value, list):
                                entity_value = ", ".join(entity_value)
                            commands_json = commands_json.replace(param_value, str(entity_value))

                # Substitute user variables
                for var_key, var_value in user_variables.items():
                    commands_json = commands_json.replace(f"{{{var_key}}}", var_value)

                # НОВОЕ: Substitute selectors from code analyzer
                if selector_context:
                    commands_json = self._substitute_selectors(commands_json, selector_context)

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

            # Format success message
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

    def _substitute_selectors(self, commands_json: str, selector_context: dict) -> str:
        """
        Substitute placeholder selectors with real ones from code analysis.
        
        Replaces patterns like:
        - {selector:username} → #username
        - {selector:password} → #password
        - {selector:submit} → [type='submit']
        """
        # Find all selector placeholders
        placeholder_pattern = r'\{selector:([a-z_]+)\}'
        
        def replace_selector(match):
            selector_name = match.group(1)
            
            # Try to find matching selector
            # 1. Check IDs first
            for id_selector in selector_context.get('ids', []):
                if selector_name in id_selector.lower():
                    return id_selector
            
            # 2. Check names
            for name_selector in selector_context.get('names', []):
                if selector_name in name_selector.lower():
                    return name_selector
            
            # 3. Fallback to generic selector
            fallback_map = {
                'username': '#username',
                'password': '#password',
                'submit': '[type="submit"]',
                'search': 'input[type="search"]',
                'date': 'input[type="date"]',
            }
            return fallback_map.get(selector_name, match.group(0))
        
        return re.sub(placeholder_pattern, replace_selector, commands_json)


# Singleton instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
