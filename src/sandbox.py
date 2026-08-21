# ============================================================
# FILE: src/sandbox.py
# PURPOSE: Isolated Python Subprocess Execution Engine
# ============================================================

import subprocess
import tempfile
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    """Structured result from a sandbox execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    timed_out: bool


# Smart input mock: when code calls input("Which hero?"), the sandbox
# prints the prompt naturally and returns an intelligent contextual answer.
# This makes generated code look like a real interactive session in the terminal.
MOCK_INPUT_HEADER = r'''
import builtins as _builtins
import sys as _sys
import re as _re

_original_input = _builtins.input
_mock_call_count = 0

def _sandboxed_input(prompt=''):
    global _mock_call_count
    _mock_call_count += 1
    if prompt:
        print(prompt, end='', flush=True)
    p_str = str(prompt)
    p_lower = p_str.lower()
    
    # 1. Loop termination guard: If called more than 4 times, or prompt is exit/quit, force break
    if _mock_call_count > 4 or any(w in p_lower for w in ['quit', 'exit', 'close']):
        for exit_val in ['5', 'q', 'exit', 'quit', 'no']:
            if exit_val in p_lower or '1-5' in p_str:
                ans = exit_val
                print(ans)
                return ans

    # 2. Handle continuation / search again prompts
    if any(w in p_lower for w in ['again', 'continue', 'another', 'more?']):
        ans = 'no' if ('yes/no' in p_lower or 'y/n' in p_lower or 'no' in p_lower) else 'exit'
        print(ans)
        return ans

    # 3. Math expression / arithmetic prompts
    if any(w in p_lower for w in ['expression', 'equation', 'formula', 'calculation', 'math problem']):
        m_expr = _re.search(r'\(.*?(?:e\.g\.|ex:?|example:?)\s*,?\s*([0-9\s+\-*/^().]+)\)', p_str, _re.I)
        if m_expr and m_expr.group(1).strip():
            ans = m_expr.group(1).strip()
            print(ans)
            return ans
        ans = '5 + 3'
        print(ans)
        return ans

    # 4. Numeric / math single-value prompts
    if any(w in p_lower for w in ['first number', 'second number', 'number', 'integer', 'radius', 'count', 'age', 'year', 'amount', 'digit', 'score', 'guess', 'width', 'height', 'celsius', 'fahrenheit']):
        ans = '5' if 'second' in p_lower else '10'
        print(ans)
        return ans

    # 5. Check ranges like (1-5) or [1-4]
    range_match = _re.search(r'\((\d+)\s*-\s*(\d+)\)|\[(\d+)\s*-\s*(\d+)\]', p_str)
    if range_match:
        # If this is a subsequent visit to the menu, choose the exit option (highest number)
        if _mock_call_count > 2:
            ans = range_match.group(2) or range_match.group(4)
        else:
            ans = range_match.group(1) or range_match.group(3)
        print(ans)
        return ans

    # 6. Check explicit options in parentheses or examples e.g. (Spider-Man, Wolverine) or (e.g. 5 + 3)
    m = _re.search(r'\(([^)]+)\)|\[([^\]]+)\]', p_str)
    if m:
        content = (m.group(1) or m.group(2)).strip()
        # If it is an example like (e.g. 5 + 3) or (ex: Batman)
        if _re.match(r'^(?:e\.g\.|ex:?|example:?|such as)', content, _re.I):
            clean_ex = _re.sub(r'^(?:e\.g\.|ex:?|example:?|such as)\s*,?\s*', '', content, flags=_re.I).strip()
            if clean_ex:
                ans = clean_ex
                print(ans)
                return ans
        elif not _re.match(r'^(?:y(?:es)?/n(?:o)?|n(?:o)?/y(?:es)?)$', content, _re.I):
            parts = [p.strip() for p in _re.split(r'[,/|]', content) if p.strip()]
            if parts:
                ans = parts[0]
                print(ans)
                return ans

    # 6. Inspect caller stack frames for database/dict keys (e.g. heroes, database, catalog)
    try:
        for depth in range(1, 5):
            try:
                frame = _sys._getframe(depth)
                for scope in [frame.f_locals, frame.f_globals]:
                    for k, v in scope.items():
                        if isinstance(v, dict) and len(v) > 0 and not k.startswith('_'):
                            keys = [str(dk) for dk in v.keys() if isinstance(dk, (str, int))]
                            if keys:
                                ans = str(keys[0])
                                print(ans)
                                return ans
            except (ValueError, AttributeError):
                break
    except Exception:
        pass

    # 7. Default fallback
    ans = 'Spider-Man'
    print(ans)
    return ans

_builtins.input = _sandboxed_input
'''


class PythonSandbox:
    """
    Executes Python code in an isolated subprocess with timeout
    and memory safety.
    """

    DEFAULT_TIMEOUT = 8

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout

    def execute(self, code: str) -> ExecutionResult:
        """
        Executes Python code in a sandboxed subprocess.
        input() calls are automatically mocked with sensible defaults
        so they print the prompt and a simulated user response.
        """
        tmp_file = None
        try:
            wrapped_code = f"{MOCK_INPUT_HEADER}\n\n# --- USER CODE ---\n{code}"

            tmp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="sandbox_",
                delete=False,
                encoding="utf-8",
            )
            tmp_file.write(wrapped_code)
            tmp_file.flush()
            tmp_file.close()

            python_exe = sys.executable or "python"
            start_time = time.perf_counter()

            result = subprocess.run(
                [python_exe, tmp_file.name],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=self.timeout,
                cwd=tempfile.gettempdir(),
                env=self._get_restricted_env(),
            )

            elapsed = time.perf_counter() - start_time

            return ExecutionResult(
                success=(result.returncode == 0),
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                exit_code=result.returncode,
                execution_time=round(elapsed, 3),
                timed_out=False,
            )

        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=(
                    f"⏱️ TIMEOUT: Execution exceeded {self.timeout}s.\n"
                    "Terminated to prevent infinite loop or recursive memory crash."
                ),
                exit_code=-1,
                execution_time=round(elapsed, 3),
                timed_out=True,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Sandbox Error: {str(e)}",
                exit_code=-2,
                execution_time=0.0,
                timed_out=False,
            )

        finally:
            if tmp_file and os.path.exists(tmp_file.name):
                try:
                    os.unlink(tmp_file.name)
                except OSError:
                    pass

    def _get_restricted_env(self) -> dict:
        """Returns a restricted environment without sensitive keys."""
        safe_env = os.environ.copy()
        sensitive_keys = [
            "GEMINI_API_KEY", "OPENAI_API_KEY", "API_KEY",
            "SECRET_KEY", "AWS_SECRET_ACCESS_KEY", "DATABASE_URL",
        ]
        for key in sensitive_keys:
            safe_env.pop(key, None)
        return safe_env
