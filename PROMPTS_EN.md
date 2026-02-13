# AI Agent Development Log: OpenEMIS Assistant

This repository focuses on building a Natural Language UI (NLUI) for educational management systems.

### Phase 1: Full-stack Infrastructure
**Goal:** Establish a communication bridge between the browser DOM and a local LLM orchestrator.

**Prompt used:**
> "I have a Python 3.13 project in PyCharm. I need a boilerplate for a Chrome Extension + FastAPI backend. Provide code for: main.py (echo server), manifest.json (V3), content.js (DOM injection), and styles.css. The extension must send fetch requests to the backend."

### Phase 2: DevOps & Dependency Management
**Goal:** Environment stabilization and secure Git workflow.

**Prompt used:**
> "Debug the SSH publickey permission denied error on macOS, set up the remote origin for the repository, and generate a requirements.txt file including fastapi and uvicorn."

### Current Progress
- [x] FastAPI server responding to async requests.
- [x] Chrome Extension successfully manipulating the DOM.
- [x] Automated dependency tracking via pip freeze.