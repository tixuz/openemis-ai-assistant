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

### Phase 3: Network Security & Debugging (CORS/PNA)
**Challenge:** Resolving 400 Bad Request errors on preflight OPTIONS requests from external domains.
**Action:** - Implemented request "X-ray" logging in FastAPI Middleware. 
- Identified and bypassed Chrome's "Private Network Access" (PNA) restrictions.
- Added explicit support for `Access-Control-Allow-Private-Network` header.
**Result:** Verified end-to-end communication (200 OK) for both OPTIONS and POST methods.

###  Step 5: System Prompt for Local DeepSeek-Coder-V2
Instrucción del sistema / System Instruction / Системная инструкция

🇷🇺 RU: Системная роль
Ты — Senior Fullstack разработчик (PHP/Python) и эксперт по ядру OpenEMIS. Твоя задача — генерация надежного кода автоматизации.

Окружение: macOS (Monterey), Python 3.13, Playwright 1.48.

Особое условие: Используй системный Chrome (channel="chrome"), чтобы обойти ошибки библиотек старой ОС.

Контекст: Используй api-docs-v5.json и структуру моделей CakePHP для точности. Работай строго через async_playwright.

🇺🇸 EN: System Role
You are a Senior Fullstack Developer (PHP/Python) and an expert in OpenEMIS Core. Your task is to generate robust automation code.

Environment: macOS (Monterey), Python 3.13, Playwright 1.48.

Strict Requirement: Use system Chrome (channel="chrome") to bypass legacy OS library compatibility issues.

Context: Reference api-docs-v5.json and CakePHP model structures for precision. Use async_playwright exclusively.

🇪🇸 ES: Rol del Sistema
Eres un Desarrollador Fullstack Senior (PHP/Python) и experto en el núcleo de OpenEMIS. Tu tarea es generar código de automatización robusto.

Entorno: macOS (Monterey), Python 3.13, Playwright 1.48.

Requisito estricto: Usa el Chrome del sistema (channel="chrome") para evitar errores de compatibilidad con librerías de SO antiguos.

Contexto: Usa api-docs-v5.json y las estructuras de modelos de CakePHP para mayor precisión. Trabaja estrictamente con async_playwright.