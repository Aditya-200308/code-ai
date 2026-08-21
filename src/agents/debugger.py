# ============================================================
# FILE: src/agents/debugger.py
# PURPOSE: Self-Repair Agent — Diagnoses Errors & Patches Code
# ============================================================

import re
from typing import Dict, Any

try:
    from src.llm_client import LLMClient
except ImportError:
    from llm_client import LLMClient


DEBUGGER_SYSTEM_PROMPT = """You are an Expert Python Debugger and Code Repair Specialist.

Fix the Python code based on the error output.

RULES:
1. Output ONLY the fixed, executable Python code. No explanations, no markdown commentary outside the code.
2. The fixed code must be complete and self-contained with all imports.
3. If the error was a KeyError, IndexError, or logic error, fix the indexing/lookup logic.
4. If the error was an infinite loop or timeout, remove 'while True' and execute the logic cleanly.
5. Use input() where interactive input is requested.
6. Keep code clean and well-structured with print() statements to show results."""


DIAGNOSIS_SYSTEM_PROMPT = """You are a Python Error Diagnostic Expert.
Analyze the error traceback and respond ONLY with a valid JSON object:
{
    "error_type": "SyntaxError|NameError|TypeError|IndexError|KeyError|TimeoutError|LogicError|Other",
    "error_line": "line number or failed statement",
    "root_cause": "one-sentence explanation of why it failed",
    "fix_strategy": "one-sentence description of how you will fix it"
}"""


class DebuggerAgent:
    """Diagnoses runtime errors and generates patched code that fixes the issue."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def diagnose(self, code: str, error_output: str) -> Dict[str, str]:
        """
        Analyzes the error traceback and returns a structured diagnosis.
        """
        user_prompt = (
            f"ORIGINAL CODE:\n```python\n{code}\n```\n\n"
            f"ERROR OUTPUT:\n```\n{error_output}\n```"
        )

        result = self.llm.generate_json(
            system_prompt=DIAGNOSIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=250,
        )

        defaults = {
            "error_type": "RuntimeError",
            "error_line": "N/A",
            "root_cause": "Execution error encountered.",
            "fix_strategy": "Applying automatic code repair.",
        }
        for key, default in defaults.items():
            if key not in result or not result[key]:
                result[key] = default

        return result

    def repair(self, code: str, error_output: str) -> str:
        """
        Takes broken code + its error output and returns fixed code.
        """
        user_prompt = (
            f"BROKEN CODE:\n{code}\n\n"
            f"ERROR OUTPUT:\n{error_output}\n\n"
            f"Generate the complete, corrected Python code that runs successfully without errors."
        )

        raw = self.llm.generate(
            system_prompt=DEBUGGER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=1500,
        )

        return self._clean_code_output(raw)

    def _clean_code_output(self, raw: str) -> str:
        """Extracts pure Python code from markdown blocks and strips preamble/postamble text."""
        raw = raw.strip()

        # 1. Match code inside ```python ... ```
        match = re.search(r"```(?:python)?\s*\n(.*?)\n```", raw, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 2. Match code inside any ``` ... ```
        match = re.search(r"```\s*\n(.*?)\n```", raw, re.DOTALL)
        if match:
            return match.group(1).strip()

        # 3. Strip standalone fences
        cleaned = re.sub(r"^```(?:python)?\s*\n?", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned, flags=re.MULTILINE)
        return cleaned.strip()
