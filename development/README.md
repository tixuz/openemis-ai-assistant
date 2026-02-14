# Development Scripts

This folder contains historical development scripts that show the evolution of the AI Automation System from initial prototype to production-ready architecture.

## 📜 Development Timeline

These scripts represent key milestones in the system's development. They are preserved for reference and educational purposes.

### Phase 1: Initial Prototyping

**`ai_agent_test.py`** - First Integration Test
- Direct connection to DeepSeek LLM (localhost:8080)
- Basic Playwright automation
- Proof of concept for AI-driven browser control
- **Key Learning**: Confirmed LLM can generate browser automation commands

**`chat.py`** - Simple Chat Interface
- Basic question-answer loop with LLM
- Port 8088 (early server configuration)
- No error handling or validation
- **Key Learning**: Established communication pattern with LLM

**`debug_chat.py`** - Debugging Version
- Added JSON response inspection
- Better error messages
- Development debugging tool
- **Key Learning**: Importance of structured logging

### Phase 2: Agent Development

**`dp_agent.py`** - Early Agent Implementation
- Integrated system prompt
- Combined LLM + Playwright execution
- Used `exec()` for code execution (⚠️ Security Issue!)
- **Key Learning**: Need for safe command execution (led to v2.0 rewrite)

**`main.py`** - Original FastAPI Application
- First API server implementation
- CORS without restrictions (⚠️ Security Issue!)
- No authentication
- Direct code execution via exec()
- **Key Learning**: Prototype worked but had critical security flaws

### Phase 3: Testing & Mocking

**`mock_llm_server.py`** - Mock LLM Server
- Returns hardcoded Playwright commands
- Instant responses (<100ms vs ~600ms)
- Used for rapid testing during development
- **Key Learning**: Fast iteration requires mocking slow dependencies

## ⚠️ Important Notes

### These Scripts Are NOT Production Code

1. **Security Issues**: Use of `exec()`, no authentication, unrestricted CORS
2. **No Validation**: Commands executed without safety checks
3. **Educational Purpose**: Show development progression and lessons learned

### What Led to v2.0 Rewrite

The experience with these prototypes revealed critical needs:
- ❌ `exec()` is dangerous → ✅ Command whitelist (v2.0)
- ❌ No auth → ✅ JWT authentication (v2.0)
- ❌ LLM generates code → ✅ LLM generates JSON (v2.0)
- ❌ No learning → ✅ Learning store with examples (v2.0)
- ❌ Monolithic file → ✅ Proper architecture (backend/frontend separation)

### Current Production Architecture

The lessons from these scripts led to the current system:
```
development/ (historical)    →    backend/ (production)
├── main.py                  →    ├── core/
├── dp_agent.py             →    │   ├── automation_engine.py (safe execution)
├── chat.py                  →    │   ├── llm_client.py (structured output)
└── (no structure)           →    │   └── learning_store.py (continuous learning)
                             →    ├── models/ (Pydantic validation)
                             →    └── api/ (proper routing, auth, RBAC)
```

## 🎓 Learning Points for Developers

If you're building a similar system, learn from our mistakes:

1. **Never use exec() in production** - Use a command whitelist instead
2. **Structure output from LLMs** - Request JSON, not code
3. **Start with security** - Auth, CORS, rate limiting from day one
4. **Mock slow dependencies** - Build mock servers for fast iteration
5. **Learn from successes** - Store and reuse successful examples (few-shot learning)
6. **Separate concerns** - Backend (API) + Frontend (UI) + Extension (client)

## 🔧 Running These Scripts (For Reference Only)

These scripts are kept for historical reference. To run them:

```bash
# Mock LLM server (still useful for testing)
cd development
python mock_llm_server.py

# Other scripts (require old dependencies)
python ai_agent_test.py
python chat.py
```

**Recommendation**: Use the production system in `backend/` and `frontend/` instead.

## 📊 Evolution Summary

| Aspect | Prototype (development/) | Production (backend/) |
|--------|-------------------------|----------------------|
| **Security** | None (exec, no auth) | JWT, whitelist, CORS, rate limiting |
| **Architecture** | Single file | Microservices (FastAPI + Flask) |
| **LLM Output** | Python code strings | Structured JSON commands |
| **Validation** | None | Pydantic models |
| **Learning** | None | JSONL-based learning store |
| **Scripts** | Not supported | Reusable script library (v2.1) |
| **Workflows** | Not supported | Natural language workflows (v2.2) |
| **Docker** | No | Multi-container (FastAPI, Flask, Redis) |
| **Testing** | Manual only | Unit + integration tests |

---

These scripts represent **6 months of learning and iteration** to build a production-ready AI automation system. They're preserved as a testament to the development journey and to help others avoid the same pitfalls.

**Current System**: See `/backend` and `/frontend` for production code.
