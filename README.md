# 🤖 AI Automation System v2.2.1

**Production-ready automation system for OpenEMIS** with safe command execution, JWT authentication, AI-powered learning, reusable scripts, and **true natural language workflows**.

[![Security](https://img.shields.io/badge/security-production--ready-green)]()
[![Architecture](https://img.shields.io/badge/architecture-microservices-blue)]()
[![AI](https://img.shields.io/badge/AI-DeepSeek%20V2-purple)]()
[![Version](https://img.shields.io/badge/version-2.2.1-blue)]()

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

### 💬 Natural Language Workflows (v2.2) 🎉🎉
- ✅ **True Natural Language** - "mark attendance, john and jack missing"
- ✅ **Intent Detection** - Understands what users want
- ✅ **Entity Extraction** - Extracts students, dates, codes automatically
- ✅ **Natural Responses** - "Attendance marked. Refresh to see." (no tech jargon!)
- ✅ **Smart 3-Tier Priority System** - Automatic execution method selection:
  1. **Workflows** - Natural language intent detection (fastest, most user-friendly)
  2. **Scripts** - Direct script execution (reliable, pre-defined)
  3. **LLM** - AI-generated commands (flexible fallback for anything)
- 📖 **[Full Documentation](docs/WORKFLOWS.md)**

### 📚 Script Library (v2.1 → v2.2.1)
- ✅ **Reusable Scripts** - Define automation once, use forever
- ✅ **Script Execution** - "run login" in chat
- ✅ **Script Chaining** - Combine scripts with AI actions
- ✅ **Parameter Support** - Scripts accept dynamic inputs
- ✅ **Script Composition** (NEW v2.2.1) - Scripts can call other scripts as parameters
- ✅ **Copy Functionality** (NEW v2.2.1) - Duplicate scripts to create variations
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
- LLM access: Local (DeepSeek, Ollama, llama.cpp) OR Cloud API (DeepSeek, Tencent Hunyuan, OpenAI, etc.)

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

**Option A: Local DeepSeek (Development)**
```bash
# Start local DeepSeek server
./start_ai.sh
# Runs on http://localhost:8080
```

**Option B: Cloud API (Production)**
```bash
# Edit docker/.env and set:
# LLM_SERVER_URL=https://api.deepseek.com/v1
# LLM_API_KEY=your-api-key

# Supported providers:
# - DeepSeek: https://api.deepseek.com/v1
# - Tencent Hunyuan: https://hunyuan.tencentcloudapi.com/v1
# - OpenAI: https://api.openai.com/v1
# - Or any OpenAI-compatible endpoint
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

**⚠️ CRITICAL - Default Credentials:**
- Username: `admin`
- Password: `admin123`

**🚨 YOU MUST CHANGE THESE BEFORE ANY DEPLOYMENT! 🚨**
- These are development-only credentials
- Never use these in production or public environments
- Update credentials in `data/users.json`

## 📖 Usage

### User Interface (Teachers / OpenEMIS Users)
1. Visit http://localhost:3000/login
2. Login with credentials
3. Go to **User Chat**
4. Talk naturally - the system understands intent:

   **Natural Language (Priority 1 - Workflows):**
   - "mark attendance, john and jack missing"
   - "go to institution P1002"
   - "search for school P1002"

   **Direct Script Execution (Priority 2 - Scripts):**
   - "run login"
   - "run openemis_login"

   **Technical Commands (Priority 3 - LLM Fallback):**
   - "Login to OpenEMIS as admin"
   - "Navigate to students page"
   - "Click the add button"

The system automatically picks the best execution method!

### Admin Panel (Prompt Engineers & Script Creators)
1. Login as admin/prompt_engineer
2. Access **Admin Dashboard**
3. **Scripts** (`/admin/scripts`): Create reusable automation scripts
4. **Run Script** (`/admin/run-script`): Execute scripts with parameters
5. **Prompt Engineering**: Edit system prompts, test generations
6. **Learning Examples**: View/manage successful automations
7. **Analytics**: Usage statistics and performance metrics
8. **User Variables**: Manage saved credentials and selectors

### Chrome Extension
1. Load extension from `extension/` folder in Chrome
2. Click 🤖 button on any webpage
3. Chat with AI for instant automation
4. Extension uses your Flask session token

## 🎯 How It Works: The 3-Tier Priority System

When you send a message, the system intelligently chooses the best execution method:

### Priority 1: Natural Language Workflows (Fastest & Most User-Friendly)
**Example:** "mark attendance, john and jack missing"

1. **Intent Detection** - Recognizes this is a MARK_ATTENDANCE intent
2. **Entity Extraction** - Extracts: students=["John", "Jack"], status="absent", date="today"
3. **Workflow Execution** - Runs predefined script chain: login → navigate_to_attendance → mark_students
4. **Natural Response** - Returns: "✅ Attendance marked. John and Jack marked absent for 2026-02-14. Refresh to see."

**Best for:** Common tasks that teachers do repeatedly (attendance, searching, reporting)

### Priority 2: Direct Script Execution (Reliable & Pre-Defined)
**Example:** "run login" or "run openemis_login"

1. **Pattern Detection** - Recognizes "run {script_name}" pattern
2. **Script Lookup** - Finds saved script in library
3. **Variable Substitution** - Fills in parameters from user variables
4. **Execution** - Runs the exact commands saved in the script

**Best for:** Technical tasks where you want exact control and repeatability

### Priority 3: LLM Fallback (Flexible & Smart)
**Example:** "Login to OpenEMIS as admin"

1. **LLM Generation** - Asks DeepSeek to generate Playwright commands
2. **Few-Shot Learning** - Injects similar examples from learning store
3. **Validation** - Checks commands against whitelist (security)
4. **Execution** - Runs generated commands
5. **Learning** - Saves successful execution for future use

**Best for:** New tasks, edge cases, or when you don't have a workflow/script defined yet

**The Beauty:** You don't choose! The system automatically picks the best method for your message. Start with natural language, and the system handles the rest.

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
│   │   ├── script_store.py       # Script storage (v2.1)
│   │   ├── workflow_engine.py    # Intent detection (v2.2)
│   │   └── prompt_manager.py     # Prompt construction
│   ├── models/          # Pydantic models
│   │   ├── commands.py           # Command whitelist
│   │   ├── auth.py               # User/JWT models
│   │   ├── learning.py           # Example schema
│   │   ├── scripts.py            # Script models (v2.1)
│   │   └── workflows.py          # Workflow models (v2.2)
│   ├── api/             # API routes
│   │   └── routes/
│   │       ├── auth.py           # Authentication
│   │       ├── automation.py     # Execute automations
│   │       ├── user.py           # User chat (3-tier priority)
│   │       ├── admin.py          # Admin panel
│   │       ├── scripts.py        # Script CRUD (v2.1)
│   │       └── variables.py      # User variables
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
│   ├── learning/        # Example storage (JSONL)
│   ├── scripts/         # Saved scripts (v2.1)
│   ├── workflows/       # Workflow definitions (v2.2)
│   ├── variables/       # User variables
│   ├── history/         # Chat history
│   └── users.json       # User database

├── docs/                # Documentation
│   ├── SCRIPT_LIBRARY.md   # Script system docs
│   └── WORKFLOWS.md        # Workflow system docs

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

### LLM Options: Local & Cloud

The system supports any OpenAI-compatible LLM endpoint. Configure via `LLM_SERVER_URL` environment variable.

#### 🏠 Local LLM (Recommended for Development)

**DeepSeek V2 (via llama.cpp)**
```bash
# Start local DeepSeek server
./start_ai.sh

# Runs on http://localhost:8080
# ~0.6s generation time (18 tokens/sec on CPU)
# ~3-5s with GPU acceleration
```

**Other Local Options:**
- **Ollama**: `ollama serve` + OpenAI-compatible endpoint
- **LM Studio**: Desktop app with OpenAI API
- **llama.cpp server**: Custom model hosting

#### ☁️ Cloud LLM (Production)

**DeepSeek API**
```bash
# DeepSeek Official API (China-based, fast, affordable)
export LLM_SERVER_URL="https://api.deepseek.com/v1"
export LLM_API_KEY="your-deepseek-api-key"

# Model: deepseek-chat (recommended)
# Pricing: ~$0.14/1M input tokens, ~$0.28/1M output tokens
```

**Tencent Hunyuan (腾讯混元)**
```bash
# Tencent Cloud AI API (China region, enterprise-grade)
export LLM_SERVER_URL="https://hunyuan.tencentcloudapi.com/v1"
export LLM_API_KEY="your-tencent-secret-id"
export LLM_SECRET_KEY="your-tencent-secret-key"

# Model: hunyuan-lite, hunyuan-standard, hunyuan-pro
# Good for: Chinese language tasks, compliance requirements
```

**OpenAI GPT**
```bash
# OpenAI Official API (Global, most capable)
export LLM_SERVER_URL="https://api.openai.com/v1"
export LLM_API_KEY="your-openai-api-key"

# Model: gpt-4-turbo, gpt-3.5-turbo
# Pricing: ~$10-30/1M tokens depending on model
```

**Other Cloud Options:**
- **Anthropic Claude**: `https://api.anthropic.com`
- **Google Gemini**: `https://generativelanguage.googleapis.com`
- **Microsoft Azure OpenAI**: `https://your-resource.openai.azure.com`
- **Alibaba Cloud**: Qwen/Tongyi models

#### 🔧 Configuration

Edit `docker/.env`:
```bash
# Local DeepSeek (default)
LLM_SERVER_URL=http://host.docker.internal:8080

# Or Cloud API
LLM_SERVER_URL=https://api.deepseek.com/v1
LLM_API_KEY=your-api-key-here
```

**Performance Comparison:**
| Option | Speed | Cost | Best For |
|--------|-------|------|----------|
| Local CPU | ~0.6s | Free | Development, privacy |
| Local GPU | ~0.2s | Free | Production (self-hosted) |
| DeepSeek API | ~0.3s | $0.14/1M tokens | Cost-effective production |
| Tencent Hunyuan | ~0.4s | ¥0.015/1K tokens | China region, compliance |
| OpenAI GPT-4 | ~0.5s | $10-30/1M tokens | Maximum quality |

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

## 📚 Documentation

Comprehensive guides are available in the `docs/` directory:

- **[SCRIPT_LIBRARY.md](docs/SCRIPT_LIBRARY.md)** - Complete guide to creating and using reusable scripts
  - Script creation workflow
  - Parameter types and composition
  - Execution methods (API, UI, Chat)
  - Security model and best practices

- **[WORKFLOWS.md](docs/WORKFLOWS.md)** - Natural language workflow system
  - Intent detection patterns
  - Entity extraction guide
  - Creating custom workflows
  - Troubleshooting and examples

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

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
- ✅ **Safe LLM code execution** - No eval/exec, command whitelist only
- ✅ **Structured output parsing** - LLM returns JSON, not code
- ✅ **Few-shot learning** - Dynamic example injection
- ✅ **Intent detection** - Natural language understanding
- ✅ **Entity extraction** - Regex-based information extraction
- ✅ **Workflow orchestration** - Multi-step automation chains
- ✅ **Script composition** - Reusable automation building blocks
- ✅ **Priority system** - Intelligent fallback (Workflows → Scripts → LLM)
- ✅ **Prompt engineering interface** - Admin panel for prompt tuning
- ✅ **JWT authentication & RBAC** - Role-based access control
- ✅ **Docker microservices** - Multi-container architecture
- ✅ **Rate limiting & security** - Production-ready safeguards

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
