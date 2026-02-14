# 🤖 AI Automation System v2.1

**Production-ready automation system for OpenEMIS** with safe command execution, JWT authentication, AI-powered learning, and **reusable script library**.

[![Security](https://img.shields.io/badge/security-production--ready-green)]()
[![Architecture](https://img.shields.io/badge/architecture-microservices-blue)]()
[![AI](https://img.shields.io/badge/AI-DeepSeek%20V2-purple)]()
[![Version](https://img.shields.io/badge/version-2.1.0-blue)]()

## 🎯 Key Features

### 🔐 Security First
- ✅ **No `exec()`** - Eliminated arbitrary code execution
- ✅ **Command Whitelist** - Only 10 safe Playwright commands allowed
- ✅ **JWT Authentication** - Role-based access control
- ✅ **Selective CORS** - localhost + demo.openemis.org only
- ✅ **Rate Limiting** - 10-20 requests/minute per IP
- ✅ **Input Validation** - Pydantic models for all data

### 🧠 AI Engineering
- ✅ **Structured Output** - LLM returns JSON, not code
- ✅ **Few-Shot Learning** - Injects successful examples
- ✅ **Learning Mechanism** - Saves executions to JSONL
- ✅ **Prompt Versioning** - Editable via admin panel
- ✅ **Error Recovery** - Retry logic with feedback

### 📚 Script Library (NEW in v2.1) 🎉
- ✅ **Reusable Scripts** - Define automation once, use forever
- ✅ **Natural Language Execution** - Say "run login" in chat
- ✅ **Script Chaining** - Combine scripts with AI actions
- ✅ **Parameter Support** - Scripts accept dynamic inputs
- ✅ **Variable Substitution** - Auto-uses saved user variables
- ✅ **Execution Tracking** - Monitor script usage stats
- 📖 **[Full Documentation](docs/SCRIPT_LIBRARY.md)**

### 🏗️ Modern Architecture
- ✅ **FastAPI Backend** - High-performance async API
- ✅ **Flask Frontend** - Clean web interfaces
- ✅ **Docker Compose** - Multi-container orchestration
- ✅ **Redis** - Session storage and rate limiting
- ✅ **Chrome Extension** - Browser integration

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Docker & Docker Compose
- Chrome browser
- DeepSeek model (or any OpenAI-compatible LLM)

### 1. Clone and Setup
```bash
cd /Users/apple/PycharmProjects/PythonProject

# Copy environment template
cp docker/.env.example docker/.env

# Edit docker/.env and set:
# - JWT_SECRET (generate with: openssl rand -hex 32)
# - FLASK_SECRET_KEY (generate with: openssl rand -hex 32)
```

### 2. Start LLM Server
```bash
# Start your DeepSeek/LLM server
./start_ai.sh

# Or use any OpenAI-compatible endpoint on port 8080
```

### 3. Start the Application
```bash
# Using the startup script (recommended)
./scripts/start_dev.sh

# Or manually with Docker Compose
cd docker
docker-compose up -d
```

### 4. Access the System
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**Default credentials:**
- Username: `admin`
- Password: `admin123` (⚠️ Change in production!)

## 📖 Usage

### User Interface (Teachers / OpenEMIS Users)
1. Visit http://localhost:3000/login
2. Login with credentials
3. Go to **User Chat**
4. Ask AI to automate tasks:
   - "Login to OpenEMIS as admin"
   - "Navigate to students page"
   - "Click the add button"

### Admin Panel (Prompt Engineers)
1. Login as admin/prompt_engineer
2. Access **Admin Dashboard**
3. **Prompt Engineering**: Edit system prompts, test generations
4. **Learning Examples**: View/manage successful automations
5. **Analytics**: Usage statistics and performance metrics

### Chrome Extension
1. Load extension from `extension/` folder in Chrome
2. Click 🤖 button on any webpage
3. Chat with AI for instant automation
4. Extension uses your Flask session token

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           User Layer                        │
├──────────────┬──────────────┬───────────────┤
│ Chrome Ext   │  Admin UI    │   User UI     │
└──────┬───────┴──────┬───────┴────────┬──────┘
       │              │                 │
       └──────────────┼─────────────────┘
                      │ JWT + CORS
       ┌──────────────▼──────────────────┐
       │   Flask (Port 3000)             │
       │   - Serves HTML                  │
       │   - Session management          │
       └──────────────┬──────────────────┘
                      │
       ┌──────────────▼──────────────────┐
       │   FastAPI (Port 8000)           │
       │   - Safe command execution       │
       │   - LLM client                   │
       │   - Learning store               │
       │   - JWT auth                     │
       └────┬──────────────┬──────────────┘
            │              │
    ┌───────▼────┐    ┌───▼───────┐
    │ Redis      │    │ Playwright│
    │ (6379)     │    │ Browser   │
    └────────────┘    └───────────┘

    External:
    ┌─────────────────────────────┐
    │ DeepSeek LLM (Port 8080)    │
    └─────────────────────────────┘
```

## 📁 Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── core/            # Business logic
│   │   ├── automation_engine.py  # Safe command executor
│   │   ├── llm_client.py         # LLM communication
│   │   ├── command_parser.py     # JSON validation
│   │   ├── learning_store.py     # Example storage
│   │   └── prompt_manager.py     # Prompt construction
│   ├── models/          # Pydantic models
│   │   ├── commands.py           # Command whitelist
│   │   ├── auth.py               # User/JWT models
│   │   └── learning.py           # Example schema
│   ├── api/             # API routes
│   │   └── routes/
│   │       ├── auth.py           # Authentication
│   │       ├── automation.py     # Execute automations
│   │       ├── user.py           # User chat
│   │       └── admin.py          # Admin panel
│   └── main.py          # FastAPI app

├── frontend/            # Flask frontend
│   ├── templates/       # Jinja2 templates
│   │   ├── admin/       # Admin interface
│   │   └── user/        # User interface
│   ├── static/          # CSS/JS
│   │   ├── css/
│   │   └── js/
│   └── app.py           # Flask app

├── extension/           # Chrome extension
│   ├── manifest.json    # Extension config
│   ├── content.js       # UI injection
│   ├── background.js    # Auth handler
│   ├── popup.html       # Extension popup
│   └── styles.css       # Styles

├── docker/              # Docker configuration
│   ├── Dockerfile.fastapi
│   ├── Dockerfile.flask
│   ├── docker-compose.yml
│   └── .env.example

├── data/                # Persistent data
│   ├── prompts/         # System prompts
│   ├── learning/        # Example storage
│   └── users.json       # User database

├── tests/               # Test suites
│   ├── unit/
│   └── integration/

└── scripts/
    └── start_dev.sh     # Development startup
```

## 🔒 Security

### What We Fixed
| Before | After |
|--------|-------|
| ❌ `exec()` runs ANY code | ✅ Only 10 whitelisted commands |
| ❌ No authentication | ✅ JWT with role-based access |
| ❌ CORS allows all origins | ✅ Only localhost + openemis.org |
| ❌ No rate limiting | ✅ 10-20 requests/min per IP |
| ❌ No input validation | ✅ Pydantic validation |

### Whitelisted Commands
Only these commands can be executed:
1. `navigate` - Go to URL (domain-validated)
2. `click` - Click element
3. `fill` - Fill input field
4. `wait_for` - Wait for element
5. `wait_for_navigation` - Wait for page load
6. `screenshot` - Take screenshot
7. `extract_text` - Get element text
8. `handle_dialog` - Accept/dismiss dialogs
9. `select_option` - Select dropdown option
10. `press_key` - Press keyboard key

### Security Disclosure
Found a security issue? Please email security@example.com or see [SECURITY.md](SECURITY.md)

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements-backend.txt

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=backend tests/
```

## 🐳 Docker + Browser Setup

### Chromium in Docker
The system runs Chromium in **headless mode** inside Docker containers:

```dockerfile
# Install to shared location accessible by non-root user
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN playwright install chromium
RUN apt-get install -y libasound2  # Required dependency
```

**Key points:**
- ✅ Browsers installed to `/opt/ms-playwright` (not `/root/.cache`)
- ✅ Using `chromium` (not `chrome`) for `playwright.chromium.launch()`
- ✅ Headless mode enabled (`headless=True` in routes)
- ✅ Non-root user (`appuser`) can access browsers

### Mock LLM Server
For fast testing without waiting for LLM inference:

```bash
# Start mock server (returns instant responses)
python3 mock_llm_server.py

# Access at http://localhost:8080
```

Mock server provides hardcoded Playwright commands for:
- Navigation: "Open OpenEMIS" → `navigate` command
- Login: "Login as admin" → 5 commands (navigate, fill username, fill password, click, wait)

**Performance:**
- Real LLM: ~0.6s generation time (18 tokens/sec on CPU)
- Mock LLM: <100ms response time
- Browser execution: ~4-9s depending on complexity

## 📊 API Documentation

### Authentication
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response: {"access_token": "...", "token_type": "bearer"}
```

### Execute Automation
```bash
curl -X POST http://localhost:8000/automation/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Login to OpenEMIS as admin", "auto_execute": false}'
```

### Admin - Update Prompt
```bash
curl -X POST http://localhost:8000/admin/prompts \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Your new system prompt..."}'
```

Full API docs: http://localhost:8000/docs

## 🛠️ Development

### Running Locally (Without Docker)
```bash
# Backend
cd backend
python -m uvicorn main:app --reload

# Frontend
cd frontend
python -m flask --app app run --port 3000
```

### View Logs
```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker-compose -f docker/docker-compose.yml logs -f fastapi
```

### Stop Services
```bash
cd docker
docker-compose down
```

## 🤝 Contributing

This project demonstrates modern AI engineering practices for portfolio/interview purposes.

**Key patterns demonstrated:**
- Safe LLM code execution (no eval/exec)
- Structured output parsing
- Few-shot learning with examples
- Prompt engineering interface
- JWT authentication & RBAC
- Docker microservices
- Rate limiting & security

## 📝 License

This project is for educational and portfolio purposes.

## 🙏 Acknowledgments

- **Playwright** - Browser automation
- **FastAPI** - Modern Python web framework
- **DeepSeek** - Local LLM inference
- **OpenEMIS** - Educational management system

---

**Built with ❤️ to showcase modern AI engineering skills**

For questions or collaboration: [Your Contact]
