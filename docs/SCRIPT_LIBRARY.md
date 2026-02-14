# Script Library - Reusable Automation Components

## Overview

The Script Library feature solves the "virgin with amnesia" problem where the AI automation agent had to regenerate commands from scratch every time. Now admins can create reusable automation scripts that can be executed via API, UI, or natural language chat.

## Key Features

- **Reusable Scripts**: Define automation workflows once, use them forever
- **Parameterized Execution**: Scripts support parameters like `{username}`, `{password}`, `{site_url}`
- **Variable Substitution**: Automatically uses saved user variables
- **Natural Language Execution**: Say "run login" in chat to execute a script
- **Script Chaining**: Combine scripts with additional AI-generated actions
- **Execution Tracking**: Track how many times each script has been run
- **Version Control**: Update scripts anytime without breaking existing workflows

## Architecture

### Components

1. **Script Store** (`backend/core/script_store.py`)
   - In-memory cache with JSONL persistence
   - CRUD operations for scripts
   - Execution counter tracking

2. **Script Models** (`backend/models/scripts.py`)
   - `AutomationScript`: Script definition with commands and parameters
   - `ScriptParameter`: Input parameter definition
   - `ScriptExecutionRequest`: Execution request with parameter values
   - `ScriptChainRequest`: Execute multiple scripts in sequence (future)

3. **API Routes** (`backend/api/routes/scripts.py`)
   - `POST /scripts` - Create new script (admin only)
   - `GET /scripts` - List all scripts (all users)
   - `GET /scripts/{name}` - Get script details
   - `PUT /scripts/{name}` - Update script (admin only)
   - `DELETE /scripts/{name}` - Delete script (admin only)
   - `POST /scripts/execute` - Execute script (all users)

4. **Chat Integration** (`backend/api/routes/user.py`)
   - Pattern detection: "run {script_name}"
   - Script + LLM chaining: "run login then do X"
   - Automatic variable substitution

5. **UI Components**
   - **Admin Script Editor** (`/admin/scripts`) - Create/edit/delete scripts
   - **Script Runner** (`/admin/run-script`) - Execute scripts with form-based parameters
   - **Chat Interface** (`/user/chat`) - Natural language script execution

## Data Storage

Scripts are stored in JSONL format at `data/scripts/scripts.jsonl`:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "openemis_login",
  "description": "Login to OpenEMIS with credentials",
  "commands": [
    {"type": "navigate", "url": "{site_url}"},
    {"type": "fill", "selector": "#username", "value": "{username}"},
    {"type": "fill", "selector": "#password", "value": "{password}"},
    {"type": "click", "selector": "button[type='submit']"},
    {"type": "wait_for_navigation", "timeout": 5000}
  ],
  "parameters": [
    {
      "name": "site_url",
      "type": "url",
      "description": "OpenEMIS site URL",
      "default_value": "https://host.docker.internal:8482/core",
      "required": true
    },
    {
      "name": "username",
      "type": "text",
      "description": "Login username",
      "required": true
    },
    {
      "name": "password",
      "type": "password",
      "description": "Login password",
      "required": true
    }
  ],
  "tags": ["authentication", "openemis", "login"],
  "created_by": "admin",
  "created_at": "2026-02-14T10:00:00Z",
  "execution_count": 42
}
```

## Usage Examples

### 1. Create Script via Admin UI

**URL:** http://localhost:3000/admin/scripts

1. Click "**+ New Script**"
2. Fill in details:
   - **Name**: `login` (alphanumeric, underscores, hyphens only)
   - **Description**: `Login to OpenEMIS`
   - **Tags**: `authentication, openemis`
3. Add parameters:
   - `username` (Text, required)
   - `password` (Password, required)
4. Write commands (JSON array):
   ```json
   [
     {"type": "navigate", "url": "https://host.docker.internal:8482/core"},
     {"type": "fill", "selector": "#username", "value": "{username}"},
     {"type": "fill", "selector": "#password", "value": "{password}"},
     {"type": "click", "selector": "button[type='submit']"},
     {"type": "wait_for_navigation", "timeout": 10000}
   ]
   ```
5. Click "**💾 Save**"

### 2. Execute Script via UI

**URL:** http://localhost:3000/admin/run-script

1. Select script from dropdown
2. Fill in required parameters
3. Check "Take screenshot after execution"
4. Click "**▶️ Run Script**"
5. View results with inline screenshots

### 3. Execute Script via Chat

**URL:** http://localhost:3000/user/chat

#### Simple execution:
```
User: "run login"
System: Executes login script, shows: "🔧 Used script: login"
```

#### Script + additional actions:
```
User: "run login then navigate to institutions"
System:
  - Executes login script
  - Generates LLM commands for "navigate to institutions"
  - Executes both
  - Shows: "🔧 Used script: login ➕ Plus additional actions"
```

#### Complex workflow:
```
User: "run login, then search for P1002, then export students, take a screenshot"
System: Chains script + LLM-generated commands
```

### 4. Execute Script via API

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}' | \
  jq -r '.access_token')

# Execute script
curl -X POST http://localhost:3000/api/scripts/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_name": "login",
    "parameters": {
      "username": "admin",
      "password": "demo"
    },
    "take_screenshot": true
  }' | jq .
```

**Response:**
```json
{
  "success": true,
  "script_name": "login",
  "response": "✅ Script 'login' executed successfully!\n\n**Commands executed:** 5\n**Time:** 8450ms\n\n📸 **Screenshot captured**\n",
  "execution_result": {
    "success": true,
    "commands_executed": 5,
    "execution_time_ms": 8450,
    "screenshots": ["logs/screenshots/screenshot_20260214_120530.png"],
    "screenshot_data": [
      {
        "filename": "screenshot_20260214_120530.png",
        "data": "iVBORw0KGgoAAAANSUhEUgAA...",
        "path": "logs/screenshots/screenshot_20260214_120530.png"
      }
    ]
  }
}
```

## Parameter Types

Scripts support the following parameter types:

- **text**: Plain text input
- **password**: Masked password input
- **url**: URL input with validation
- **selector**: CSS selector input
- **number**: Numeric input

## Variable Substitution

Scripts automatically substitute:

1. **Script parameters**: `{username}`, `{password}`, `{site_url}`
2. **User variables**: `{my_username}`, `{my_password}`, `{my_site}`

If a user has saved variables that match script parameters, they are automatically used:

```json
// User has saved variable: my_username = "admin"
// Script parameter: {username}

// When script is executed:
{"type": "fill", "selector": "#username", "value": "{username}"}
// Becomes:
{"type": "fill", "selector": "#username", "value": "admin"}
```

## Chat Pattern Detection

The system detects the following patterns in chat messages:

1. `"run {script_name}"` → Execute script
2. `"run {script_name} script"` → Execute script
3. `"execute {script_name}"` → Execute script
4. `"run {script_name} then X"` → Execute script + LLM-generated commands for X

Regex patterns used:
```python
patterns = [
    r'run\s+(?:the\s+)?(\w+)\s+script',
    r'execute\s+(?:the\s+)?(\w+)\s+script',
    r'run\s+(\w+)',
    r'execute\s+(\w+)',
]
```

## Security

### Script Creation
- **Admin only**: Only users with `admin` or `prompt_engineer` role can create/edit/delete scripts
- **Name validation**: Script names must match `^[a-zA-Z0-9_-]+$` (alphanumeric, underscores, hyphens)
- **Command validation**: All commands are validated against the whitelist in `backend/models/commands.py`

### Script Execution
- **All authenticated users**: Any logged-in user can execute scripts
- **Parameter validation**: Required parameters must be provided
- **Command validation**: Commands are validated before execution via Pydantic models
- **Domain whitelist**: Navigate commands only allow whitelisted domains

### Best Practices
1. Don't hardcode credentials in scripts - use parameters
2. Use descriptive parameter names: `{username}`, not `{u}`
3. Add descriptions to parameters for clarity
4. Use tags to organize scripts by category
5. Test scripts thoroughly before sharing with users

## Common Use Cases

### 1. Login Workflow
```json
{
  "name": "openemis_login",
  "description": "Login to OpenEMIS",
  "commands": [
    {"type": "navigate", "url": "{site_url}"},
    {"type": "fill", "selector": "#username", "value": "{username}"},
    {"type": "fill", "selector": "#password", "value": "{password}"},
    {"type": "click", "selector": "button[type='submit']"},
    {"type": "wait_for_navigation"}
  ]
}
```

### 2. Navigation Script
```json
{
  "name": "go_to_institution",
  "description": "Navigate to specific institution",
  "commands": [
    {"type": "click", "selector": "#Institutions-Institutions-index"},
    {"type": "fill", "selector": "#search-searchfield", "value": "{institution_code}"},
    {"type": "press_key", "key": "Enter"},
    {"type": "wait_for", "selector": ".search-results"}
  ]
}
```

### 3. Data Export Script
```json
{
  "name": "export_students",
  "description": "Export student list as CSV",
  "commands": [
    {"type": "click", "selector": "#Students-Students-index"},
    {"type": "wait_for", "selector": ".students-table"},
    {"type": "click", "selector": ".export-csv-button"},
    {"type": "screenshot"}
  ]
}
```

## Future Enhancements

### Script Chaining (Planned)
Execute multiple scripts in sequence with persistent browser context:

```bash
POST /scripts/chain
{
  "scripts": [
    {
      "script_name": "openemis_login",
      "parameters": {"username": "admin", "password": "demo"}
    },
    {
      "script_name": "go_to_institution",
      "parameters": {"institution_code": "P1002"}
    },
    {
      "script_name": "export_students",
      "parameters": {}
    }
  ],
  "session_name": "my_workflow"
}
```

### Session Persistence (Planned)
Keep browser context alive between script executions to:
- Avoid re-authentication
- Speed up workflows
- Share cookies/localStorage between scripts

### Script Versioning (Planned)
- Track script changes over time
- Rollback to previous versions
- Compare script versions

### Script Marketplace (Planned)
- Share scripts with other users
- Import scripts from community library
- Rate and review scripts

## Troubleshooting

### Script not found in chat
**Problem:** Say "run mylogin" but system doesn't find it
**Solution:** Script names are case-sensitive. Check exact name in `/admin/scripts`

### Parameters not substituting
**Problem:** `{username}` appears literally in commands
**Solution:** Ensure parameter name matches exactly. Check for typos.

### Script executes but fails
**Problem:** Script runs but automation fails
**Solution:**
- Check selectors are correct for your OpenEMIS version
- Increase timeout values if pages load slowly
- Add `wait_for` commands before clicking elements

### Can't see scripts in chat
**Problem:** Type "run login" but no response
**Solution:** Ensure script is saved in `/admin/scripts` first

## API Reference

See [API_REFERENCE.md](./API_REFERENCE.md) for complete API documentation.

## Contributing

When adding new features to Script Library:

1. Update models in `backend/models/scripts.py`
2. Add storage methods in `backend/core/script_store.py`
3. Create API routes in `backend/api/routes/scripts.py`
4. Update UI in `frontend/templates/admin/scripts.html`
5. Add tests in `tests/integration/test_scripts.py`
6. Update this documentation

## License

See main project LICENSE file.
