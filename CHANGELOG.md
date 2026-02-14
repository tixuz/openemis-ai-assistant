# Changelog

All notable changes to this project will be documented in this file.

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
