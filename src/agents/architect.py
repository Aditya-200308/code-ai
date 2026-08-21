# ============================================================
# FILE: src/agents/architect.py
# PURPOSE: Code Generation Agent — Transforms Natural Language to Python
# ============================================================

try:
    from src.llm_client import LLMClient
except ImportError:
    from llm_client import LLMClient


ARCHITECT_SYSTEM_PROMPT = """You are an expert Python Software Engineer.

Write COMPLETE, PRODUCTION-READY, EXECUTABLE Python code that precisely fulfills the user's task.

RULES:
1. Return ONLY pure Python code. No introductory text, no markdown, no commentary outside the code.
2. Write natural, idiomatic Python. Use input() where the task implies interactive user input (e.g. "when asked", "let the user choose", "ask which").
3. When using input(), ask ONE question, get ONE answer, and display the result for ONLY that answer. Do NOT loop through all data or dump everything.
4. Keep data compact (2-4 entries max) to stay within token limits.
5. The code must be 100% complete and self-contained with all imports included.
6. Do NOT use while True infinite loops. A single input() call followed by a lookup and print is ideal."""


class ArchitectAgent:
    """Generates complete, executable Python code from natural language prompts."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_code(self, user_request: str) -> str:
        """
        Takes a natural language description and returns executable Python code.
        """
        raw = self.llm.generate(
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            user_prompt=(
                f"Task: {user_request}\n\n"
                "Write complete Python code with formatted print output."
            ),
            temperature=0.1,
            max_tokens=1500,
        )

        code = self._clean_code_output(raw)
        return code

    def _clean_code_output(self, raw: str) -> str:
        """Extracts pure Python code from markdown blocks and strips preamble/postamble text."""
        import re
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
