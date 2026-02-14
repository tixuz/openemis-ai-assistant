# Changelog

All notable changes to this project will be documented in this file.

## [2.2.1] - 2026-02-14

### Added - Script Composition & Copy 🎉

**Enhanced Script Library with True Reusability**

Scripts can now call other scripts and be easily duplicated!

#### New Features
- **Script as Parameter Type**: Scripts can accept other scripts as parameters for composition
  - Example: Create a "complete_workflow" script that calls "login", "navigate_to_page", and "submit_form" scripts
  - Enables true modular automation building blocks

- **Copy Script Functionality**: One-click duplication of existing scripts
  - Copies all parameters, commands, tags, and descriptions
  - Automatically appends "_copy" to the name for easy identification
  - Perfect for creating variations of similar automations

#### Updated Components
- `backend/models/scripts.py` - Added "script" to parameter type enum
- `frontend/templates/admin/scripts.html` - Added Copy Script button and functionality
- `frontend/templates/admin/run_script.html` - Added dropdown for script-type parameters

#### Usage Examples
```json
{
  "name": "complete_onboarding",
  "parameters": [
    {"name": "login_script", "type": "script", "required": true},
    {"name": "setup_script", "type": "script", "required": true}
  ],
  "commands": [
    {"type": "execute_script", "script_name": "{login_script}"},
    {"type": "execute_script", "script_name": "{setup_script}"},
    {"type": "navigate", "url": "/dashboard"}
  ]
}
```

#### UI Improvements
- Script parameter dropdown shows available scripts
- Copy button appears when editing existing scripts
- Copied scripts automatically get "_copy" suffix

---

## [2.2.0] - 2026-02-14

### Added - Natural Language Workflows 🎉🎉

**The "Better World" Vision - True Natural Language Automation**

Teachers can now speak naturally instead of using technical commands!

#### Before (Technical):
```
Teacher: "run login then navigate to attendance page"
System: ✅ Executed 5 commands in 8450ms
```

#### After (Natural):
```
Teacher: "mark attendance, john and jack missing"
System: ✅ Attendance marked. John and Jack marked absent. Refresh the page to see.
```

#### Core Features
- **Intent Detection**: Recognizes user intent from natural language
- **Entity Extraction**: Automatically extracts students, dates, codes from messages
- **Workflow Orchestration**: Maps intents to script chains
- **Natural Responses**: Returns human-friendly confirmations (no technical details)
- **Priority System**: Workflows → Scripts → LLM (smart fallback)

#### New Components
- `backend/models/workflows.py` - Workflow and intent models
- `backend/core/workflow_engine.py` - Intent detection and workflow execution
  - `IntentDetector` - Pattern matching and entity extraction
  - `WorkflowStore` - Workflow definition storage
  - `WorkflowEngine` - Orchestrates workflow execution
- `docs/WORKFLOWS.md` - Complete workflow documentation

#### Supported Intents
1. **MARK_ATTENDANCE** - "mark attendance, john and jack absent"
   - Extracts: students, date, status
   - Executes: login → navigate_to_attendance → mark_students
   - Returns: "✅ Attendance marked. John, Jack marked absent for 2026-02-14. Refresh to see."

2. **SEARCH_INSTITUTION** - "go to institution P1002"
   - Extracts: institution_code
   - Executes: login → navigate_to_institutions → search_institution
   - Returns: "✅ Found institution P1002. Displaying details."

3. **CHECK_HOMEWORK** (Planned) - "check who submitted math homework"
4. **EXPORT_GRADES** (Planned) - "export grades for class 5A"

#### Entity Extraction Capabilities
- **Student Names**: "john and jack", "John Smith", "john, jack, and mary"
- **Dates**: "today", "yesterday", "2026-02-14"
- **Status**: "absent", "missing" → "absent"; "present" → "present"
- **Institution Codes**: "P1002", "P-1002"

#### Chat Integration
Enhanced `backend/api/routes/user.py` with priority system:
1. **Try Workflow** - Natural language intent detection
2. **Try Script** - Direct script execution ("run login")
3. **Try LLM** - Generate commands for unknown requests

#### Updated Components
- `backend/api/routes/user.py` - Added workflow engine integration

#### Workflow Definition Format
```json
{
  "intent_type": "MARK_ATTENDANCE",
  "steps": [
    {"script_name": "login", "parameters": {}},
    {"script_name": "mark_students", "parameters": {"students": "{students}"}}
  ],
  "success_message": "✅ Attendance marked. {students} marked {status}.",
  "requires_entities": ["students", "status"]
}
```

#### Storage
- Workflows: `data/workflows/workflows.jsonl`
- Intent patterns: `INTENT_PATTERNS` in code
- Default workflows: `DEFAULT_WORKFLOWS`

#### Use Cases
```
"mark today's attendance, john and jack are absent"
"go to institution P1002"
"search for school P1002"
"mark john present"
```

### Technical Details
- Pattern-based intent detection (keyword matching)
- Entity extraction with regex patterns
- In-memory workflow caching
- Automatic variable substitution from user variables
- Human-friendly response formatting

### Documentation
- Added `docs/WORKFLOWS.md` - Complete workflow system documentation
- Usage examples and troubleshooting guide
- Entity extraction patterns
- Creating custom workflows

---

## [2.1.0] - 2026-02-14

### Added - Script Library Feature 🎉

**Major New Feature: Reusable Automation Scripts**

Solves the "virgin with amnesia" problem - the AI no longer forgets previous automations!

#### Core Features
- **Script Library** (`/admin/scripts`): Create, edit, and manage reusable automation scripts
- **Script Runner UI** (`/admin/run-script`): Execute scripts with form-based parameter input
- **Chat Integration**: Execute scripts via natural language (e.g., "run login")
- **Script Chaining**: Combine scripts with AI-generated actions (e.g., "run login then navigate to institutions")
- **Variable Substitution**: Scripts automatically use saved user variables
- **Execution Tracking**: Track how many times each script has been executed

#### New Components
- `backend/models/scripts.py` - Script data models (AutomationScript, ScriptParameter, etc.)
- `backend/core/script_store.py` - Script storage with in-memory cache + JSONL persistence
- `backend/api/routes/scripts.py` - REST API for script management and execution
- `frontend/templates/admin/scripts.html` - Admin UI for script creation/editing
- `frontend/templates/admin/run_script.html` - User-friendly script execution interface
- `docs/SCRIPT_LIBRARY.md` - Comprehensive documentation

#### Updated Components
- `backend/api/routes/user.py` - Added script detection and execution in chat
  - Pattern detection: "run {script_name}", "execute {script_name}"
  - Chaining support: "run {script} then do X"
  - Automatic variable substitution
- `frontend/templates/base.html` - Added navigation links for Scripts and Run Script
- `backend/main.py` - Registered scripts router

#### API Endpoints
- `POST /scripts` - Create script (admin only)
- `GET /scripts` - List all scripts
- `GET /scripts/{name}` - Get script details
- `PUT /scripts/{name}` - Update script (admin only)
- `DELETE /scripts/{name}` - Delete script (admin only)
- `POST /scripts/execute` - Execute script (all authenticated users)

#### Usage Examples
```bash
# Chat: Natural language execution
"run login"
"run login then navigate to institutions"

# API: Programmatic execution
curl -X POST /api/scripts/execute \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"script_name": "login", "parameters": {"username": "admin"}}'
```

### Fixed
- **Run Script UI**: Fixed result display issue - execution results and screenshots now display correctly
- **Docker networking**: Added `host.docker.internal` to domain whitelist for accessing host services from containers
- **Flask routing**: Fixed admin_scripts endpoint registration

### Changed
- Chat interface now shows available scripts when user types "run" without a script name
- Response messages indicate when a saved script was used (🔧 icon)
- Variable substitution order: script parameters first, then user variables

### Technical Details
- Script storage format: JSONL at `data/scripts/scripts.jsonl`
- In-memory caching for fast script lookup
- Pydantic validation for all commands
- Supports parameter types: text, password, url, selector, number
- Scripts inherit full security model (domain whitelist, command validation)

### Documentation
- Added `docs/SCRIPT_LIBRARY.md` - Complete feature documentation
- Added usage examples and troubleshooting guide
- Documented API endpoints and request/response formats

---

## [2.0.0] - 2026-02-13

### Added - Production-Ready Architecture

**Complete System Rewrite**

#### Security Improvements
- ✅ **Eliminated `exec()`**: Replaced arbitrary code execution with safe command validation
- ✅ **JWT Authentication**: Added proper authentication with role-based access control
- ✅ **CORS Protection**: Restricted to localhost + openemis.org domains
- ✅ **Rate Limiting**: 10 automations per minute per IP
- ✅ **Input Validation**: Pydantic models for all commands

#### Architecture Changes
- **Backend (FastAPI)**: Port 8000
  - Safe command execution engine (no exec)
  - Learning mechanism (JSONL storage)
  - LLM client with structured output
  - User variables system
  - Command history tracking

- **Frontend (Flask)**: Port 3000
  - Admin interface (prompt engineering, examples, analytics)
  - User interface (chat, variables)
  - API proxy to FastAPI

- **Docker Compose**: Multi-container setup
  - FastAPI container (backend)
  - Flask container (frontend)
  - Redis container (sessions, rate limiting)

#### New Features
- **User Variables System** (`/user/variables`): Save credentials and selectors for reuse
- **Learning Store**: Automatically saves successful automations for few-shot learning
- **Chat History**: Persistent conversation history per user
- **Screenshot Display**: Inline base64-encoded screenshots in chat responses
- **Detailed Response Formatting**: Shows exact commands executed with emojis

#### Command Whitelist
Only these commands are allowed:
- `navigate` - Navigate to URL (domain whitelist enforced)
- `click` - Click element by selector
- `fill` - Fill input field
- `wait_for` - Wait for element to appear
- `wait_for_navigation` - Wait for page load
- `screenshot` - Take screenshot
- `extract_text` - Extract text from element
- `handle_dialog` - Accept/dismiss browser dialogs
- `select_option` - Select dropdown option
- `press_key` - Press keyboard key

#### Data Storage
- Learning examples: `data/learning/examples.jsonl`
- Chat history: `data/history/{username}_history.jsonl`
- User variables: `data/variables/{username}/variables.json`
- System prompts: `data/prompts/system_prompt.txt`

### Changed
- LLM now returns JSON commands instead of Python code
- Context size increased: 2048 → 4096 tokens
- Browser runs in headless mode (required for Docker)
- All file paths are absolute (not relative)

### Fixed
- Docker networking: Use `host.docker.internal:PORT` to access host machine from container
- Memory management: Conversation history properly tracked
- Screenshot encoding: Base64 for inline display

---

## [1.0.0] - 2026-01-XX

### Initial Release

- Basic automation with DeepSeek LLM
- Chrome extension for browser automation
- Playwright-based command execution
- Python code generation (unsafe - used exec)
- Simple prompt system

**⚠️ Security Warning**: This version used `exec()` for code execution and had no authentication.
