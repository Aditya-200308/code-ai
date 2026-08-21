# ⚡ CodeAI — Autonomous Coding & Sandbox Execution Agent

> **Portfolio Project #03** | An autonomous closed-loop code generation system with isolated subprocess sandboxing, self-diagnosing error repair, and Google Gemini Flash Cloud AI.

[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Google Gemini](https://img.shields.io/badge/Gemini_Flash-Cloud_AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)

---

## 🌟 Architecture Overview

CodeAI implements an autonomous **closed-loop** code generation and self-repair pipeline:

```
[User Prompt] ➔ [1. Architect Agent] ➔ [2. Sandbox Executor]
                                              │
                      ✅ Success ◄────────────┤
                                               │
                      ❌ Error ────────────────┘
                            │
                            ▼
                    [3. Debugger Agent] ➔ Diagnose ➔ Patch ➔ Re-Execute
                            │                              (Max 3 loops)
                            ▼
                    [4. Output Visualizer]
```

### 🤖 The 3 Specialized Stages
1. **🧠 Architect Agent** — Transforms natural language into complete, executable Python programs via Google Gemini Flash.
2. **🔒 Sandbox Executor** — Runs code in an isolated subprocess with timeout enforcement, safe `input()` context injection, and memory safety.
3. **🔧 Debugger Agent** — Reads tracebacks, analyzes root cause, synthesizes code patches, and loops back into the sandbox.

---

## ⚡ Key Features
* **Subprocess Isolation**: Code runs in a separate child process — infinite loops are terminated, API keys are stripped.
* **Autonomous Self-Healing**: Configurable repair attempts (1–3 iterations) with structured JSON error diagnosis.
* **Instant Cloud Generation**: Sub-2.5s generation powered by Google Gemini Flash multi-model rotation.
* **Interactive Suggestion Chips**: 1-click test cases for algorithms, simulations, and data analysis.
* **Full Telemetry**: Every pipeline step logged with timestamps, agent attribution, and execution metrics.

---

## 🚀 Quickstart

### 1. Clone & Install:
```bash
git clone https://github.com/YOUR_USERNAME/code-ai.git
cd code-ai
pip install -r requirements.txt
```

### 2. Configure Environment:
Create a `.env` file or export your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Launch:
```bash
streamlit run app.py
```

---

## 🌐 Deploy to Streamlit Cloud

1. Push this repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub repository.
4. Set **Main file path**: `app.py`
5. Under **Advanced Settings** ➔ **Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key"
   ```
6. Click **Deploy!** 🚀
