# Natural Language Workflows - Intent-Based Automation

## Overview

The Workflow system enables **true natural language automation** where users can say things like:

```
"mark today's attendance, john and jack are absent"
```

Instead of technical commands like:
```
"run login then navigate_to_attendance then mark_students_absent"
```

## The Better World Vision ✨

### Before (Technical):
```
Teacher: "run login then navigate to attendance page then fill in form"
System: ✅ Executed 5 commands in 8450ms
```

### After (Natural):
```
Teacher: "mark attendance, john and jack missing"
System: ✅ Attendance marked. John and Jack marked absent for 2026-02-14. Refresh the page to see.
```

The system:
1. **Understands intent** - Recognizes "mark attendance"
2. **Extracts entities** - Finds students (john, jack) and status (missing)
3. **Maps to scripts** - Knows which script chain to run
4. **Executes workflow** - Runs login → navigate → mark_students scripts
5. **Returns naturally** - "Attendance marked. Refresh to see." (not technical details)

## Architecture

### Components

1. **Intent Detector** (`IntentDetector`)
   - Matches message against known intent patterns
   - Extracts entities (students, dates, codes, etc.)
   - Returns confidence score

2. **Workflow Store** (`WorkflowStore`)
   - Stores workflow definitions in JSONL
   - Maps intents to script chains
   - Provides default workflows

3. **Workflow Engine** (`WorkflowEngine`)
   - Orchestrates workflow execution
   - Substitutes entities into script parameters
   - Returns user-friendly messages

4. **Integration** (`user.py` chat endpoint)
   - Priority order: Workflows → Scripts → LLM
   - Seamless fallback if no workflow matches

### Data Flow

```
User Message
    ↓
Intent Detection (keyword matching + entity extraction)
    ↓
Workflow Lookup (find script chain for intent)
    ↓
Entity Substitution (inject extracted data into scripts)
    ↓
Script Chain Execution (login → navigate → action)
    ↓
Natural Response ("Attendance marked. Refresh to see.")
```

## Supported Intents

### 1. MARK_ATTENDANCE
**Purpose:** Mark students as present or absent

**Entities:**
- `students` (List[str]) - Student names
- `date` (str) - Date in YYYY-MM-DD format
- `status` (str) - "present" or "absent"

**Examples:**
```
"mark attendance, john and jack are absent"
"john is missing today"
"mark john and sarah present"
"mark today's attendance, john absent"
```

**Workflow:**
1. Execute `login` script
2. Execute `navigate_to_attendance` with {date}
3. Execute `mark_students` with {students} and {status}

**Response:**
```
✅ Attendance marked. John, Jack marked absent for 2026-02-14. Refresh the page to see changes.
```

### 2. SEARCH_INSTITUTION
**Purpose:** Find and navigate to institution by code

**Entities:**
- `institution_code` (str) - Institution code (e.g., P1002)

**Examples:**
```
"go to institution P1002"
"search for school P1002"
"open institution P1002"
"find institution P-1002"
```

**Workflow:**
1. Execute `login` script
2. Execute `navigate_to_institutions` script
3. Execute `search_institution` with {institution_code}

**Response:**
```
✅ Found institution P1002. Displaying details.
```

### 3. CHECK_HOMEWORK (Planned)
**Purpose:** View homework submission status

**Entities:**
- `students` (List[str]) - Student names (optional)
- `subject` (str) - Subject name (optional)
- `date` (str) - Due date

**Examples:**
```
"check who submitted math homework"
"show homework status for john"
"check today's homework submissions"
```

### 4. EXPORT_GRADES (Planned)
**Purpose:** Export grades as CSV

**Entities:**
- `class` (str) - Class name
- `subject` (str) - Subject name
- `period` (str) - Grading period

**Examples:**
```
"export grades for class 5A"
"download math grades as csv"
"export semester grades"
```

## Workflow Definition

Workflows are stored in `data/workflows/workflows.jsonl`:

```json
{
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
      "script_name": "mark_students",
      "parameters": {
        "students": "{students}",
        "status": "{status}"
      },
      "description": "Mark student attendance"
    }
  ],
  "success_message": "✅ Attendance marked. {students} marked {status} for {date}. Refresh the page to see changes.",
  "error_message": "❌ Failed to mark attendance. Please try again or mark manually.",
  "requires_entities": ["students", "status"],
  "examples": [
    "mark today's attendance, john and jack are absent",
    "mark attendance, john missing",
    "john and jack are absent today"
  ]
}
```

## Entity Extraction

### Student Names
**Patterns:**
- Capitalized words: "John", "Jack"
- After keywords: "absent: john and jack"
- In context: "john and jack are absent"

**Examples:**
```
"mark attendance, john and jack missing" → ["John", "Jack"]
"john is absent" → ["John"]
"John Smith and Mary Jane absent" → ["John Smith", "Mary Jane"]
```

### Dates
**Patterns:**
- Relative: "today", "yesterday", "tomorrow"
- Absolute: "2026-02-14", "14/02/2026"

**Examples:**
```
"mark today's attendance" → "2026-02-14"
"yesterday's attendance" → "2026-02-13"
"mark attendance for 2026-02-15" → "2026-02-15"
```

### Status
**Patterns:**
- Keywords: "absent", "missing" → "absent"
- Keywords: "present" → "present"
- Default: "absent" (if students mentioned without status)

**Examples:**
```
"john is absent" → "absent"
"mark john present" → "present"
"john and jack" → "absent" (default)
```

### Institution Code
**Patterns:**
- Format: `[A-Z]\d{4}` or `[A-Z]-?\d{4}`

**Examples:**
```
"go to P1002" → "P1002"
"institution P-1002" → "P-1002"
"search for school P1234" → "P1234"
```

## Usage Examples

### Example 1: Mark Attendance

**Pre-requisites:**
Admin must create these scripts:
1. `login` - Login to OpenEMIS
2. `navigate_to_attendance` - Open attendance page
3. `mark_students` - Mark students absent/present

**User says:**
```
"mark today's attendance, john and jack are missing"
```

**System processing:**
1. Intent detected: `MARK_ATTENDANCE`
2. Entities extracted:
   - students: ["John", "Jack"]
   - date: "2026-02-14"
   - status: "absent"
3. Workflow found: Mark Student Attendance
4. Scripts executed:
   - login()
   - navigate_to_attendance(date="2026-02-14")
   - mark_students(students="John, Jack", status="absent")
5. Response returned:

```
✅ Attendance marked. John, Jack marked absent for 2026-02-14. Refresh the page to see changes.
```

### Example 2: Search Institution

**Pre-requisites:**
Admin must create these scripts:
1. `login` - Login to OpenEMIS
2. `navigate_to_institutions` - Open institutions page
3. `search_institution` - Search by code

**User says:**
```
"go to institution P1002"
```

**System processing:**
1. Intent detected: `SEARCH_INSTITUTION`
2. Entities extracted:
   - institution_code: "P1002"
3. Workflow found: Search Institution
4. Scripts executed:
   - login()
   - navigate_to_institutions()
   - search_institution(code="P1002")
5. Response returned:

```
✅ Found institution P1002. Displaying details.
```

## Integration with Chat

The chat endpoint tries methods in this priority order:

1. **Workflow Intent Detection** (natural language)
   ```
   "mark attendance, john missing" → Execute workflow
   ```

2. **Script Execution** (semi-technical)
   ```
   "run login" → Execute script directly
   ```

3. **LLM Generation** (fallback for unknown requests)
   ```
   "navigate to students page" → Generate commands via LLM
   ```

This ensures maximum flexibility while preferring structured workflows for common tasks.

## Creating Custom Workflows

### Step 1: Create Required Scripts

First, create the individual scripts that your workflow will use:

```python
# Example: Create "mark_students" script
POST /scripts
{
  "name": "mark_students",
  "description": "Mark students as absent or present",
  "commands": [
    {"type": "click", "selector": "#attendance-tab"},
    {"type": "fill", "selector": "#student-names", "value": "{students}"},
    {"type": "click", "selector": "input[value='{status}']"},
    {"type": "click", "selector": "#save-attendance"}
  ],
  "parameters": [
    {"name": "students", "type": "text", "required": true},
    {"name": "status", "type": "text", "required": true}
  ]
}
```

### Step 2: Define Workflow

Add workflow to `data/workflows/workflows.jsonl`:

```json
{
  "intent_type": "MARK_ATTENDANCE",
  "name": "Mark Attendance",
  "description": "Mark student attendance",
  "steps": [
    {"script_name": "login", "parameters": {}},
    {"script_name": "navigate_to_attendance", "parameters": {"date": "{date}"}},
    {"script_name": "mark_students", "parameters": {"students": "{students}", "status": "{status}"}}
  ],
  "success_message": "✅ Attendance marked. {students} marked {status}.",
  "error_message": "❌ Could not mark attendance.",
  "requires_entities": ["students", "status"]
}
```

### Step 3: Add Intent Pattern (Optional)

To improve detection, add pattern to `INTENT_PATTERNS` in `backend/models/workflows.py`:

```python
INTENT_PATTERNS = {
    "MARK_ATTENDANCE": {
        "keywords": ["mark", "attendance", "absent", "missing", "present"],
        "entities": ["students", "date", "status"],
        "examples": [
            "mark attendance, john is absent",
            "john and jack are missing today"
        ]
    }
}
```

## Security

### Intent Detection
- Only recognizes pre-defined intents
- Requires minimum keyword matches (2+)
- Entity extraction uses strict patterns

### Workflow Execution
- All workflows use existing scripts (already validated)
- Scripts undergo full command validation
- Same security model as script execution

### Entity Injection
- Entities are validated before substitution
- No arbitrary code execution
- Domain whitelist still enforced

## Troubleshooting

### Intent Not Detected

**Problem:** Say "mark attendance" but system doesn't recognize it

**Solutions:**
1. Check if keywords match patterns in `INTENT_PATTERNS`
2. Add more keywords: "mark attendance absent john"
3. Check logs: `docker logs ai-automation-fastapi | grep intent`

### Missing Entities

**Problem:** System says "Missing required information: students"

**Solutions:**
1. Be more explicit: "mark attendance for john" → "mark attendance, john is absent"
2. Use names after keywords: "absent: john and jack"
3. Capitalize names: "John" instead of "john"

### Workflow Executes But Fails

**Problem:** Workflow runs but returns error

**Solutions:**
1. Check if required scripts exist: GET /scripts
2. Verify script parameters match workflow step parameters
3. Check script selectors are correct for your OpenEMIS version
4. Check logs for detailed error messages

### Falls Back to LLM Instead of Workflow

**Problem:** System generates commands instead of using workflow

**Solutions:**
1. Ensure message contains enough keywords (2+)
2. Check workflow exists: `cat data/workflows/workflows.jsonl`
3. Verify intent type matches pattern
4. Add more examples to workflow definition

## Future Enhancements

### 1. LLM-Based Intent Detection
Replace keyword matching with LLM classification:
```python
intent = await llm.classify_intent(message)
entities = await llm.extract_entities(message, intent)
```

### 2. Conversation Context
Remember previous messages:
```
User: "mark attendance"
System: "For which date and students?"
User: "today, john and jack absent"
System: ✅ Attendance marked...
```

### 3. Confirmation Dialogs
Ask before executing:
```
User: "mark attendance, john absent"
System: "Mark John as absent for today (2026-02-14)? Reply 'yes' to confirm."
User: "yes"
System: ✅ Attendance marked.
```

### 4. Workflow Templates
Create workflows via UI:
- Drag-and-drop script steps
- Define entity mappings
- Test with sample inputs

### 5. Multi-Language Support
Detect intents in multiple languages:
```
User: "marcar asistencia, john ausente" (Spanish)
System: ✅ Asistencia marcada...
```

## API Reference

### Detect Intent (Internal)
```python
from backend.core.workflow_engine import get_workflow_engine

engine = get_workflow_engine()
intent = await engine.intent_detector.detect_intent("mark attendance, john absent")

# Returns:
WorkflowIntent(
    intent_type="MARK_ATTENDANCE",
    entities={"students": ["John"], "status": "absent", "date": "2026-02-14"},
    confidence=0.75,
    original_message="mark attendance, john absent"
)
```

### Execute Workflow
```python
workflow_found, execution = await engine.execute_from_message(
    message="mark attendance, john absent",
    user=user,
    variables_store=variables_store
)

if workflow_found:
    print(execution.message)
    # Output: ✅ Attendance marked. John marked absent for 2026-02-14. Refresh the page to see changes.
```

## Contributing

To add new workflows:

1. Define intent pattern in `backend/models/workflows.py`
2. Create required scripts via `/admin/scripts`
3. Add workflow definition to `data/workflows/workflows.jsonl`
4. Test with example phrases
5. Update this documentation

## License

See main project LICENSE file.
