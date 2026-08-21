# ============================================================
# FILE: src/app.py
# PURPOSE: Code AI — Autonomous Coding Agent Dashboard
# ============================================================

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
for p in [current_dir, parent_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
import time
import html as html_lib

try:
    from src.orchestrator import CodingOrchestrator, PipelineState
    from src.sandbox import PythonSandbox, ExecutionResult
except ImportError:
    from orchestrator import CodingOrchestrator, PipelineState
    from sandbox import PythonSandbox, ExecutionResult

# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="Code AI | Autonomous Coding Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================================================================
# SESSION STATE DEFAULTS
# ================================================================
for key, default in [
    ("engine_mode", "cloud_turbo"),
    ("max_repairs", 2),
    ("pipeline_state", None),
    ("run_count", 0),
    ("input_text", ""),
    ("task_input_field", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ================================================================
# STYLING — High-Contrast Cyber Terminal IDE with Custom Tabs
# ================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #08080c !important;
        color: #e2e8f0;
    }

    .stMarkdown, .stMarkdown p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.02rem;
        color: #e2e8f0;
    }

    code, pre, .stCode, .stCode pre, .stCode code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.02rem !important;
        line-height: 1.65 !important;
    }

    /* ─── Canvas & Header: Deep Obsidian ─── */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: #08080c !important;
    }

    /* ─── Protect Streamlit Native Menus from Text Distortion ─── */
    [data-testid="stHeader"] *,
    [data-baseweb="popover"] *,
    [data-baseweb="menu"] *,
    div[role="dialog"] *,
    div[role="menu"] * {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: normal !important;
    }

    /* ─── Hide default sidebar completely ─── */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* ─── Hide "Press Enter / Ctrl+Enter" helper text ─── */
    [data-testid="InputInstructions"],
    [data-testid="stFormInstructions"],
    [data-testid="stTextInputInstructions"],
    .stTextInput small,
    .stTextArea small,
    div[data-testid="stMarkdownContainer"] small {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* ─── Navigation Tabs Bar (Consistent with Portfolio Standards) ─── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem !important;
        background: #0d0f18 !important;
        border-bottom: 2px solid #1e2235 !important;
        padding: 0.4rem 0.6rem 0 0.6rem !important;
        border-radius: 12px 12px 0 0 !important;
        margin-bottom: 1.4rem !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 0.75rem 1.4rem !important;
        border-bottom: 3px solid transparent !important;
        transition: all 0.25s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #00f0ff !important;
        background: rgba(0, 240, 255, 0.06) !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 240, 255, 0.12) !important;
        color: #00f0ff !important;
        border-bottom: 3px solid #00f0ff !important;
    }

    /* ─── Top Toolbar & Brand Header ─── */
    .toolbar-brand {
        display: inline-flex;
        align-items: center;
        gap: 0.75rem;
    }
    .toolbar-brand .logo {
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        letter-spacing: -0.5px;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .toolbar-brand .logo-accent {
        background: linear-gradient(135deg, #00f0ff 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .toolbar-badge {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        color: #00ff9d !important;
        background: rgba(0, 255, 157, 0.12);
        border: 1px solid rgba(0, 255, 157, 0.35);
        padding: 0.28rem 0.7rem;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: 0.8px;
        white-space: nowrap;
    }

    /* ─── Prompt Header ─── */
    .prompt-header-title {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #00f0ff !important;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }

    /* ─── Thicker Search Bar ─── */
    .stTextInput div[data-baseweb="base-input"],
    .stTextInput div[data-baseweb="input"],
    .stTextInput div[data-testid="stTextInputRootElement"] {
        background: #0f111a !important;
        border: 2px solid #282e44 !important;
        border-radius: 16px !important;
        min-height: 76px !important;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.25s ease !important;
    }
    .stTextInput div[data-baseweb="input"]:focus-within {
        border-color: #00f0ff !important;
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.35) !important;
    }
    .stTextInput input {
        background: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.3rem !important;
        line-height: 1.6 !important;
        padding: 1.4rem 1.8rem !important;
        min-height: 72px !important;
    }
    .stTextInput input:focus {
        border: none !important;
        box-shadow: none !important;
    }
    .stTextInput input::placeholder {
        color: #64748b !important;
        font-size: 1.18rem !important;
    }

    /* Remove form container border */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }

    /* ─── Suggestion Chips ─── */
    .stButton > button {
        background: #121522 !important;
        border: 1px solid #262c42 !important;
        color: #38bdf8 !important;
        border-radius: 10px !important;
        font-size: 0.98rem !important;
        font-weight: 600 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        padding: 0.6rem 1.1rem !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        background: rgba(0, 240, 255, 0.15) !important;
        border-color: #00f0ff !important;
        color: #ffffff !important;
        box-shadow: 0 0 16px rgba(0, 240, 255, 0.25) !important;
        transform: translateY(-1px) !important;
    }

    /* ─── Action Button (Centered & Electric Cyan Gradient) ─── */
    .stFormSubmitButton > button,
    button[kind="primary"],
    button[data-testid="stFormSubmitButton"],
    button[data-testid="baseButton-secondaryFormSubmit"],
    button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #00f0ff 0%, #7c3aed 100%) !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.15rem !important;
        letter-spacing: 0.5px !important;
        padding: 0.95rem 2.4rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 25px rgba(0, 240, 255, 0.3) !important;
        transition: all 0.25s ease !important;
    }
    .stFormSubmitButton > button:hover,
    button[kind="primary"]:hover,
    button[data-testid="stFormSubmitButton"]:hover,
    button[data-testid="baseButton-secondaryFormSubmit"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #00f0ff 20%, #9333ea 100%) !important;
        box-shadow: 0 6px 32px rgba(0, 240, 255, 0.5) !important;
        transform: translateY(-2px) !important;
    }

    /* ─── Radio & Select Controls ─── */
    .stRadio label {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #cbd5e1 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stSelectbox div[data-baseweb="select"] {
        background: #0f111a !important;
        border: 1px solid #262c42 !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }

    /* ─── Status Bar ─── */
    .status-bar {
        display: flex;
        align-items: center;
        gap: 1.8rem;
        padding: 0.8rem 1.4rem;
        background: #0f111a;
        border: 1px solid #1e2235;
        border-radius: 12px;
        margin: 1.2rem 0 0.8rem 0;
        overflow-x: auto;
    }
    .status-item {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.98rem !important;
        white-space: nowrap;
    }
    .status-label {
        color: #64748b !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        font-size: 0.82rem !important;
        letter-spacing: 0.8px;
    }
    .status-value {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
    }
    .status-value-pass {
        color: #00ff9d !important;
        font-weight: 800 !important;
    }
    .status-value-fail {
        color: #ff4d4d !important;
        font-weight: 800 !important;
    }
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-dot-green {
        background: #00ff9d;
        box-shadow: 0 0 10px #00ff9d;
    }
    .status-dot-red {
        background: #ff4d4d;
        box-shadow: 0 0 10px #ff4d4d;
    }

    /* ─── Editor & Terminal Panes ─── */
    .pane-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1.2rem;
        background: #111422;
        border: 1px solid #222738;
        border-bottom: none;
        border-radius: 12px 12px 0 0;
        margin-top: 0.8rem;
    }
    .pane-title {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        color: #00f0ff !important;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .pane-subtitle {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.88rem !important;
        color: #64748b !important;
    }

    .terminal {
        background: #06070a;
        border: 1px solid #222738;
        border-top: none;
        border-radius: 0 0 12px 12px;
        padding: 1.4rem;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.05rem !important;
        line-height: 1.75 !important;
        color: #00ff9d !important;
        white-space: pre-wrap;
        word-break: break-word;
        min-height: 220px;
        box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
    }
    .terminal-error {
        color: #ff6b6b !important;
    }
    .terminal-prompt {
        color: #475569 !important;
        font-weight: 600 !important;
        user-select: none;
    }

    /* ─── Architecture Visualizer Cards ─── */
    .arch-flow-container {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem 0;
    }
    .arch-step-card {
        background: #0f111a;
        border: 1px solid #222738;
        border-radius: 14px;
        padding: 1.2rem 1.6rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.25s ease;
    }
    .arch-step-card:hover {
        border-color: #00f0ff;
        transform: translateY(-2px);
    }
    .arch-step-header {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.4rem;
    }
    .arch-step-num {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 800;
        font-size: 1.1rem;
        color: #64748b;
    }
    .arch-step-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    .arch-step-desc {
        font-size: 0.98rem;
        color: #94a3b8;
        line-height: 1.6;
    }
    .arch-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.5px;
    }
    .arch-badge-cyan { background: rgba(0, 240, 255, 0.12); color: #00f0ff; border: 1px solid rgba(0, 240, 255, 0.3); }
    .arch-badge-purple { background: rgba(168, 85, 247, 0.12); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    .arch-badge-green { background: rgba(0, 255, 157, 0.12); color: #00ff9d; border: 1px solid rgba(0, 255, 157, 0.3); }
    .arch-badge-amber { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

    .arch-flow-arrow {
        text-align: center;
        font-size: 1.4rem;
        color: #00f0ff;
        font-weight: 800;
        line-height: 1;
        margin: 0.75rem 0;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
    }
    .arch-branch-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    .arch-branch-card {
        background: #0f111a;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        border: 1px solid #222738;
    }
    .arch-branch-pass { border-left: 4px solid #00ff9d; }
    .arch-branch-repair { border-left: 4px solid #f59e0b; }
    .arch-branch-title { font-weight: 700; font-size: 1.1rem; color: #f1f5f9; margin-bottom: 0.35rem; }

    /* ─── Repair & Diagnosis Cards ─── */
    .repair-card {
        background: #111422;
        border: 1px solid #222738;
        border-left: 4px solid #a855f7;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.3rem;
        margin: 0.6rem 0;
    }
    .repair-label {
        font-size: 0.85rem !important;
        color: #00f0ff !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 800 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .repair-value {
        font-size: 1.08rem !important;
        color: #f1f5f9 !important;
        margin-top: 0.35rem;
        line-height: 1.5;
        font-weight: 500;
    }

    /* ─── Log Panel ─── */
    .log-panel {
        background: #0a0c14;
        border: 1px solid #222738;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        max-height: 380px;
        overflow-y: auto;
    }
    .log-line {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 0.6rem 0;
        font-size: 1.02rem !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .log-line:last-child { border-bottom: none; }
    .log-ts {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
        color: #64748b !important;
        min-width: 70px;
        flex-shrink: 0;
    }
    .log-agent {
        font-size: 0.95rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        color: #38bdf8 !important;
        font-weight: 700 !important;
        min-width: 110px;
        flex-shrink: 0;
    }
    .log-msg {
        color: #cbd5e1 !important;
        flex: 1;
        line-height: 1.5;
    }
    .log-msg strong {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* ─── Bigger & Bolder Main Tabs (Code Lab, Execution Log, etc.) ─── */
    div[data-testid="stTabs"] [role="tablist"] {
        gap: 0.85rem !important;
        padding: 0.4rem 0 0.8rem 0 !important;
        border-bottom: 2px solid #1e2235 !important;
    }
    div[data-testid="stTabs"] button[role="tab"],
    button[data-testid="stTab"],
    div[data-baseweb="tab-list"] button {
        font-size: 1.22rem !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        padding: 0.85rem 1.8rem !important;
        border-radius: 12px 12px 0 0 !important;
        background: #0d101d !important;
        border: 1.5px solid #22273d !important;
        border-bottom: none !important;
        color: #94a3b8 !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover,
    button[data-testid="stTab"]:hover,
    div[data-baseweb="tab-list"] button:hover {
        color: #ffffff !important;
        background: #181f33 !important;
        border-color: #38bdf8 !important;
        transform: translateY(-1px) !important;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
    button[data-testid="stTab"][aria-selected="true"],
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #00f0ff !important;
        background: #14192b !important;
        border-color: #00f0ff !important;
        border-bottom: 3.5px solid #00f0ff !important;
        font-weight: 800 !important;
        box-shadow: 0 -4px 18px rgba(0, 240, 255, 0.2) !important;
    }
    div[data-testid="stTabs"] button[role="tab"] p,
    button[data-testid="stTab"] p {
        font-size: 1.22rem !important;
        font-weight: 700 !important;
    }

    /* ─── Download buttons ─── */
    .stDownloadButton > button {
        background: #1e1b4b !important;
        border: 1.5px solid #6366f1 !important;
        color: #c7d2fe !important;
        font-weight: 700 !important;
        font-size: 1.02rem !important;
        border-radius: 10px !important;
        padding: 0.65rem 1.4rem !important;
    }
    .stDownloadButton > button:hover {
        background: #312e81 !important;
        border-color: #818cf8 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)


# ================================================================
# TOP TOOLBAR HEADER (Centered Tech Brand & Subtitle)
# ================================================================
t_left, t_center, t_right = st.columns([0.8, 5.2, 1.4], vertical_alignment="center")

with t_center:
    st.markdown("""
    <div style="text-align: center; padding: 0.2rem 0 0.6rem 0;">
        <div class="toolbar-brand" style="justify-content: center; margin-bottom: 0.35rem;">
            <span style="font-size: 2rem; color: #00f0ff; text-shadow: 0 0 16px rgba(0, 240, 255, 0.6); font-family: 'JetBrains Mono', monospace; font-weight: 800; line-height: 1;">&lt;/&gt;</span>
            <span class="logo">Code <span class="logo-accent">AI</span></span>
            <span class="toolbar-badge">⚡ GOOGLE GEMINI FLASH ACTIVE</span>
            <span class="toolbar-badge" style="background: rgba(16, 185, 129, 0.12); color: #34d399; border-color: rgba(16, 185, 129, 0.3);">SANDBOX READY</span>
        </div>
        <div style="font-size: 1.05rem; color: #94a3b8; font-weight: 500; font-family: 'Plus Jakarta Sans', sans-serif;">
            Autonomous Closed-Loop Python Code Synthesis, Sandbox Execution & Self-Repair Engine
        </div>
    </div>
    """, unsafe_allow_html=True)

with t_right:
    st.session_state["max_repairs"] = st.selectbox(
        "Max Repairs",
        [1, 2, 3],
        index=st.session_state.get("max_repairs", 2) - 1,
        format_func=lambda x: f"🔄 {x} Repair Attempt{'s' if x > 1 else ''}",
        label_visibility="collapsed",
        key="rep_select_top",
    )
st.session_state["engine_mode"] = "cloud_turbo"


# ================================================================
# MAIN NAVIGATION TABS (Structured & Organized Views)
# ================================================================
tab_lab, tab_history, tab_debug, tab_arch = st.tabs([
    "🧪 Code Lab",
    "📜 Execution Log",
    "🔧 Debug & Self-Repair",
    "🏗️ Architecture Flow",
])


# ─── TAB 1: CODE LAB (Primary Workbench) ──────────────────────
with tab_lab:
    st.markdown("""
    <div style="margin-top: 0.4rem;">
        <div class="prompt-header-title">$ PROMPT_INPUT // Describe what to build (press Enter to run):</div>
    </div>
    """, unsafe_allow_html=True)

    # Suggestion chips
    auto_prompt = None
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🔐 Password Checker", use_container_width=True, key="chip_pwd"):
            auto_prompt = "Build a password strength checker function that tests 3 passwords and prints ratings"
    with c2:
        if st.button("📊 Sales Data Analyzer", use_container_width=True, key="chip_sales"):
            auto_prompt = "Create a sales data analyzer that calculates totals, averages, and prints a formatted summary"
    with c3:
        if st.button("🧮 Sort Algorithm Race", use_container_width=True, key="chip_sort"):
            auto_prompt = "Write a program that benchmarks bubble sort vs merge sort on random numbers and prints results"
    with c4:
        if st.button("🎲 Dice Monte Carlo", use_container_width=True, key="chip_dice"):
            auto_prompt = "Create a Monte Carlo dice simulator that rolls two dice 100000 times and prints probability distribution"

    if auto_prompt:
        st.session_state["task_input_field"] = auto_prompt
        st.session_state["input_text"] = auto_prompt
        st.session_state["auto_run_prompt"] = auto_prompt
        st.rerun()

    # Single-line Form: ENTER key immediately triggers run!
    with st.form(key="prompt_form", clear_on_submit=False):
        user_task = st.text_input(
            "Code Prompt Input",
            placeholder="e.g. Build a calculator that performs math operations on sample values and prints results...",
            label_visibility="collapsed",
            key="task_input_field",
        )

        col_left, col_btn, col_right = st.columns([1, 1.4, 1])
        with col_btn:
            run_clicked = st.form_submit_button(
                "⚡ Generate & Execute Program",
                type="primary",
                use_container_width=True,
            )

    task_to_run = ""
    run_triggered = False

    if st.session_state.get("auto_run_prompt"):
        task_to_run = st.session_state.pop("auto_run_prompt")
        run_triggered = True
    elif run_clicked:
        task_to_run = user_task.strip()
        run_triggered = bool(task_to_run)
        if not task_to_run:
            st.warning("⚠️ Please provide a prompt describing what you want to build.")

    if run_triggered and task_to_run:
        st.session_state["run_count"] += 1
        st.session_state["input_text"] = task_to_run

        with st.spinner("🧠 Architect Agent is synthesizing and testing code in sandbox..."):
            try:
                orch = CodingOrchestrator(engine_mode="cloud_turbo")
                state = orch.run_pipeline(
                    task=task_to_run,
                    max_repairs=st.session_state["max_repairs"],
                )
                st.session_state["pipeline_state"] = state
            except Exception as e:
                st.error(f"❌ Pipeline Execution Error: {e}")

    # ─── Live Results & Split Pane ───
    state = st.session_state.get("pipeline_state")
    if state and state.final_status != "PENDING":
        is_pass = state.final_status == "SUCCESS"
        dot_class = "status-dot-green" if is_pass else "status-dot-red"
        status_text = "EXECUTION PASSED" if is_pass else "EXECUTION FAILED"
        status_val_class = "status-value-pass" if is_pass else "status-value-fail"

        result = state.current_result
        exec_time = f"{result.execution_time}s" if result else "—"
        lines = len(state.current_code.splitlines()) if state.current_code else 0
        version = len(state.code_versions)

        st.markdown(f"""
        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot {dot_class}"></span>
                <span class="{status_val_class}">{status_text}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Gen Time:</span>
                <span class="status-value">{state.generation_time}s</span>
            </div>
            <div class="status-item">
                <span class="status-label">Sandbox Exec:</span>
                <span class="status-value">{exec_time}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Repairs Used:</span>
                <span class="status-value">{state.repair_count}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Code Length:</span>
                <span class="status-value">{lines} lines</span>
            </div>
            <div class="status-item">
                <span class="status-label">Version:</span>
                <span class="status-value">v{version}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Engine:</span>
                <span class="status-value">Google Gemini Flash</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_code, col_term = st.columns([1.1, 0.9])

        with col_code:
            v_label = f"v{version}" if version == 1 else f"v{version} (self-repaired)"
            st.markdown(f"""
            <div class="pane-header">
                <span class="pane-title">📝 main.py</span>
                <span class="pane-subtitle">{v_label} · {lines} lines</span>
            </div>
            """, unsafe_allow_html=True)
            st.code(state.current_code, language="python", line_numbers=True)

        with col_term:
            if is_pass and result:
                st.markdown("""
                <div class="pane-header">
                    <span class="pane-title" style="color: #00ff9d;">💻 Sandbox Terminal Output</span>
                    <span class="pane-subtitle">stdout (exit 0)</span>
                </div>
                """, unsafe_allow_html=True)
                stdout = html_lib.escape(result.stdout or "(Program executed with no stdout output)")
                st.markdown(f"""
                <div class="terminal">
<span class="terminal-prompt">$ python main.py</span>
{stdout}</div>
                """, unsafe_allow_html=True)

            elif not is_pass and result:
                st.markdown("""
                <div class="pane-header">
                    <span class="pane-title" style="color: #ff4d4d;">❌ Sandbox Error Traceback</span>
                    <span class="pane-subtitle">stderr</span>
                </div>
                """, unsafe_allow_html=True)
                stderr = html_lib.escape(result.stderr or "Unknown runtime error occurred")
                st.markdown(f"""
                <div class="terminal terminal-error">
<span class="terminal-prompt">$ python main.py</span>
{stderr}</div>
                """, unsafe_allow_html=True)

        if state.current_code:
            dl1, dl2, _ = st.columns([1.2, 1.2, 2.6])
            with dl1:
                st.download_button(
                    "📥 Download Python File (.py)",
                    data=state.current_code,
                    file_name="code_ai_output.py",
                    mime="text/x-python",
                    use_container_width=True,
                )
            with dl2:
                if result and result.stdout:
                    st.download_button(
                        "📤 Download Execution Output (.txt)",
                        data=result.stdout,
                        file_name="output.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )




# ─── TAB 2: EXECUTION LOG ─────────────────────────────────────
with tab_history:
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <div style="font-size: 1.3rem; font-weight: 700; color: #ffffff;">📜 Pipeline Execution Log</div>
        <div style="font-size: 0.95rem; color: #64748b; margin-top: 0.2rem;">Every agent action, execution step, and timing telemetry logged chronologically.</div>
    </div>
    """, unsafe_allow_html=True)

    state = st.session_state.get("pipeline_state")
    if state and state.logs:
        log_html = ""
        for entry in state.logs:
            agent = entry.get("agent", "")
            log_html += (
                f'<div class="log-line">'
                f'<span class="log-ts">{entry["time"]}</span>'
                f'<span class="log-agent">{agent}</span>'
                f'<span class="log-msg"><strong>{entry["icon"]} {entry["title"]}</strong> {entry.get("detail", "")}</span>'
                f'</div>'
            )
        st.markdown(f'<div class="log-panel">{log_html}</div>', unsafe_allow_html=True)
    else:
        st.info("No executions yet. Run a prompt in the **Code Lab** tab to view live agent logs!")


# ─── TAB 3: DEBUG & SELF-REPAIR TRACE ─────────────────────────
with tab_debug:
    st.markdown("""
<div style="margin-bottom: 1rem;">
    <div style="font-size: 1.3rem; font-weight: 700; color: #ffffff;">🔧 Self-Repair Diagnostic Trace</div>
    <div style="font-size: 0.95rem; color: #64748b; margin-top: 0.2rem;">Automated error diagnosis, root cause analysis, and code repair iterations.</div>
</div>
""", unsafe_allow_html=True)

    state = st.session_state.get("pipeline_state")
    if state and state.diagnoses:
        for i, diag in enumerate(state.diagnoses, 1):
            st.markdown(f'<div style="font-family: \'JetBrains Mono\', monospace; font-size: 1.15rem; color: #c084fc; font-weight: 700; margin: 1rem 0 0.5rem 0;">// Repair Iteration #{i}</div>', unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f'<div class="repair-card"><div class="repair-label">Error Classification</div><div class="repair-value">{diag.get("error_type", "Unknown")}</div></div><div class="repair-card"><div class="repair-label">Root Cause Analysis</div><div class="repair-value">{diag.get("root_cause", "N/A")}</div></div>', unsafe_allow_html=True)
            with d2:
                st.markdown(f'<div class="repair-card"><div class="repair-label">Offending Code / Line</div><div class="repair-value">{diag.get("error_line", "N/A")}</div></div><div class="repair-card"><div class="repair-label">Fix Strategy Applied</div><div class="repair-value">{diag.get("fix_strategy", "N/A")}</div></div>', unsafe_allow_html=True)
            if i < len(state.code_versions):
                with st.expander(f"📄 View Patched Code (v{i + 1})", expanded=False):
                    st.code(state.code_versions[i], language="python", line_numbers=True)

    elif state and state.final_status == "SUCCESS" and state.repair_count == 0:
        st.markdown("""
<div style="text-align: center; padding: 3rem 1rem; background: #0f111a; border-radius: 14px; border: 1px solid #1e2235;">
    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✨</div>
    <div style="font-size: 1.3rem; font-weight: 700; color: #00ff9d;">PERFECT FIRST PASS</div>
    <div style="font-size: 1rem; color: #94a3b8; margin-top: 0.4rem;">The code executed in the sandbox on the first try with 0 errors. No self-repair was needed!</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.info("No repair traces yet. When code throws a runtime error, the Debugger Agent's step-by-step diagnostic breakdown will appear here.")


# ─── TAB 4: ARCHITECTURE FLOW (Clean Visual Cards) ───────────
with tab_arch:
    st.markdown("""
<div style="margin-bottom: 1.5rem;">
    <div style="font-size: 1.4rem; font-weight: 800; color: #ffffff;">🏗️ Autonomous Closed-Loop Architecture</div>
    <div style="font-size: 1rem; color: #64748b; margin-top: 0.2rem;">How the Architect Agent, Subprocess Sandbox, and Debugger Agent collaborate to synthesize and self-repair code.</div>
</div>

<div class="arch-step-card">
    <div class="arch-step-header">
        <span class="arch-step-num">01</span>
        <span class="arch-step-title">👤 Natural Language Prompt</span>
        <span class="arch-badge arch-badge-cyan">INPUT</span>
    </div>
    <div class="arch-step-desc">
        User specifies what program, algorithm, or data transformation script they want to build in plain English.
    </div>
</div>

<div class="arch-flow-arrow">▼</div>

<div class="arch-step-card">
    <div class="arch-step-header">
        <span class="arch-step-num">02</span>
        <span class="arch-step-title">🧠 Architect Agent (Code Synthesis)</span>
        <span class="arch-badge arch-badge-purple">GENERATION</span>
    </div>
    <div class="arch-step-desc">
        Deconstructs requirements, selects appropriate algorithms, and generates self-contained Python code powered by Google Gemini Flash.
    </div>
</div>

<div class="arch-flow-arrow">▼</div>

<div class="arch-step-card">
    <div class="arch-step-header">
        <span class="arch-step-num">03</span>
        <span class="arch-step-title">🔒 Isolated Subprocess Sandbox</span>
        <span class="arch-badge arch-badge-green">EXECUTION</span>
    </div>
    <div class="arch-step-desc">
        Executes the Python script in an isolated subprocess with 8-second timeout enforcement, stdin context injection, and environment variable stripping.
    </div>
</div>

<div class="arch-flow-arrow">▼</div>

<!-- Decision Gate Card -->
<div style="background: #111422; border: 1.5px dashed #6366f1; border-radius: 14px; padding: 1.1rem 1.6rem; margin: 0.4rem 0;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem;">
        <span style="font-size: 1.15rem; font-weight: 800; color: #a5b4fc; font-family: 'JetBrains Mono', monospace;">⚖️ CONDITIONAL DECISION GATE // Execution Evaluation</span>
        <span class="arch-badge" style="background: rgba(99, 102, 241, 0.15); color: #c7d2fe; border: 1px solid #6366f1;">BRANCHING LOGIC</span>
    </div>
    <div class="arch-step-desc">
        After running in the sandbox, the pipeline checks the exit code. The execution takes <strong>one of two mutually exclusive paths</strong> (they do not happen at the same time):
    </div>
</div>

<div class="arch-flow-arrow">▼</div>

<div class="arch-branch-container">
    <div class="arch-branch-card arch-branch-pass">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
            <div class="arch-branch-title" style="color: #00ff9d; margin-bottom: 0;">✅ Path A: Direct Pass (Exit Code 0)</div>
            <span class="arch-badge arch-badge-green">IF SUCCESS</span>
        </div>
        <div class="arch-step-desc">
            Program executed with zero runtime or syntax errors. <strong>Bypasses the repair loop entirely</strong> and routes verified code & stdout straight to Delivery.
        </div>
    </div>
    <div class="arch-branch-card arch-branch-repair">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
            <div class="arch-branch-title" style="color: #f59e0b; margin-bottom: 0;">🔄 Path B: Self-Repair Feedback Loop</div>
            <span class="arch-badge arch-badge-amber">IF ERROR (UP TO 3x)</span>
        </div>
        <div class="arch-step-desc">
            If an error or timeout occurs, the <strong>Debugger Agent</strong> intercepts stderr, extracts root cause, patches code, and <strong>loops back to Stage 03 (Sandbox)</strong> to re-verify.
        </div>
    </div>
</div>

<div class="arch-flow-arrow">▼</div>

<div class="arch-step-card">
    <div class="arch-step-header">
        <span class="arch-step-num">04</span>
        <span class="arch-step-title">📤 Telemetry & Final Delivery</span>
        <span class="arch-badge arch-badge-amber">DELIVERY</span>
    </div>
    <div class="arch-step-desc">
        Displays verified source code, live sandbox terminal output, generation latency, lines of code, repair history, and downloadable deliverables.
    </div>
</div>
""", unsafe_allow_html=True)
