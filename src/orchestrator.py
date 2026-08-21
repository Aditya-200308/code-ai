# ============================================================
# FILE: src/orchestrator.py
# PURPOSE: Autonomous Generate → Execute → Debug Pipeline
# ============================================================

import time
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass, field

try:
    from src.llm_client import LLMClient
    from src.sandbox import PythonSandbox, ExecutionResult
    from src.agents.architect import ArchitectAgent
    from src.agents.debugger import DebuggerAgent
except ImportError:
    from llm_client import LLMClient
    from sandbox import PythonSandbox, ExecutionResult
    from agents.architect import ArchitectAgent
    from agents.debugger import DebuggerAgent


@dataclass
class PipelineState:
    """Tracks the complete state of a code generation pipeline run."""

    task: str = ""
    max_repairs: int = 2

    # Code versions (index 0 = original, 1+ = repairs)
    code_versions: List[str] = field(default_factory=list)
    execution_results: List[ExecutionResult] = field(default_factory=list)
    diagnoses: List[Dict[str, str]] = field(default_factory=list)

    # Timing
    generation_time: float = 0.0
    total_time: float = 0.0

    # Status
    final_status: str = "PENDING"  # PENDING | SUCCESS | FAILED
    repair_count: int = 0

    # Step-by-step log for UI
    logs: List[Dict[str, str]] = field(default_factory=list)

    def log(self, agent: str, icon: str, title: str, detail: str = ""):
        """Adds a timestamped log entry."""
        self.logs.append({
            "agent": agent,
            "icon": icon,
            "title": title,
            "detail": detail,
            "time": time.strftime("%H:%M:%S"),
        })

    @property
    def current_code(self) -> str:
        """Returns the latest code version."""
        return self.code_versions[-1] if self.code_versions else ""

    @property
    def current_result(self) -> Optional[ExecutionResult]:
        """Returns the latest execution result."""
        return self.execution_results[-1] if self.execution_results else None


class CodingOrchestrator:
    """
    Orchestrates the autonomous coding pipeline:
    Generate Code → Execute in Sandbox → [Debug & Repair] → Final Output

    The self-repair loop runs up to `max_repairs` times before giving up.
    """

    def __init__(self, api_key: Optional[str] = None, engine_mode: str = "cloud_turbo"):
        self.llm = LLMClient(api_key=api_key, engine_mode=engine_mode)
        self.architect = ArchitectAgent(self.llm)
        self.debugger = DebuggerAgent(self.llm)
        self.sandbox = PythonSandbox(timeout=8)

    def run_pipeline(
        self,
        task: str,
        max_repairs: int = 2,
        on_step: Optional[Callable[[PipelineState], None]] = None,
    ) -> PipelineState:
        """
        Runs the full autonomous coding pipeline.
        """
        state = PipelineState(task=task, max_repairs=max_repairs)
        pipeline_start = time.perf_counter()

        # ─── STEP 1: GENERATE CODE ─────────────────────────────
        state.log("Orchestrator", "⚡", "Pipeline Started",
                  f"Task: '{task}' | Max Repairs: {max_repairs}")
        self._notify(on_step, state)

        state.log("Architect", "🧠", "Generating Code",
                  "Synthesizing complete Python script with test cases...")
        self._notify(on_step, state)

        gen_start = time.perf_counter()
        try:
            code = self.architect.generate_code(task)
            state.generation_time = round(time.perf_counter() - gen_start, 2)
        except Exception as e:
            state.generation_time = round(time.perf_counter() - gen_start, 2)
            state.final_status = "FAILED"
            state.log("Architect", "❌", "Code Generation Failed", str(e))
            state.total_time = round(time.perf_counter() - pipeline_start, 2)
            self._notify(on_step, state)
            return state

        state.code_versions.append(code)
        state.log("Architect", "✅", "Code Generated",
                  f"Generated {len(code.splitlines())} lines in {state.generation_time}s")
        self._notify(on_step, state)

        # ─── STEP 2: EXECUTE IN SANDBOX ────────────────────────
        state.log("Sandbox", "🔒", "Executing Code",
                  "Running in isolated subprocess with 8s timeout...")
        self._notify(on_step, state)

        result = self.sandbox.execute(code)
        state.execution_results.append(result)

        # Success with stdout output
        if result.success and result.stdout.strip():
            state.final_status = "SUCCESS"
            state.log("Sandbox", "✅", "Execution Successful",
                      f"Completed in {result.execution_time}s | Exit code: 0")
            state.total_time = round(time.perf_counter() - pipeline_start, 2)
            self._notify(on_step, state)
            return state

        # If it succeeded with exit code 0 but produced no stdout, trigger demonstration repair
        if result.success and not result.stdout.strip():
            state.log("Sandbox", "ℹ️", "No Output Detected",
                      "Code executed but printed nothing. Debugger will attach demonstration queries...")
            self._notify(on_step, state)
            error_reason = (
                "The code executed successfully with exit code 0, but produced NO stdout output. "
                "Please add demonstration test calls and print() statements at the bottom "
                "to execute the functions/classes and display formatted results."
            )
        else:
            state.log("Sandbox", "❌", "Execution Failed",
                      f"Exit code: {result.exit_code} | "
                      f"{'TIMEOUT' if result.timed_out else 'RUNTIME ERROR'}")
            self._notify(on_step, state)
            error_reason = result.stderr

        # ─── STEP 3: SELF-REPAIR LOOP ──────────────────────────
        for attempt in range(1, max_repairs + 1):
            state.repair_count = attempt

            state.log("Debugger", "🔧", f"Repair Attempt {attempt}/{max_repairs}",
                      "Diagnosing root cause and synthesizing patch...")
            self._notify(on_step, state)

            current_code = state.current_code

            try:
                diagnosis = self.debugger.diagnose(current_code, error_reason)
            except Exception:
                diagnosis = {
                    "error_type": "MissingOutput" if result.success else "RuntimeError",
                    "root_cause": "Program lacks demonstration test calls" if result.success else "Runtime crash",
                    "fix_strategy": "Adding test queries and formatted print statements",
                }

            state.diagnoses.append(diagnosis)
            state.log("Debugger", "🔍", f"Diagnosis: {diagnosis.get('error_type', 'Unknown')}",
                      diagnosis.get("root_cause", ""))
            self._notify(on_step, state)

            # Generate repaired code
            try:
                fixed_code = self.debugger.repair(current_code, error_reason)
            except Exception as e:
                state.log("Debugger", "❌", "Repair Failed", str(e))
                self._notify(on_step, state)
                continue

            state.code_versions.append(fixed_code)

            # Re-execute the fixed code
            state.log("Sandbox", "🔒", f"Re-executing (Attempt {attempt})",
                      "Running patched code in sandbox...")
            self._notify(on_step, state)

            result = self.sandbox.execute(fixed_code)
            state.execution_results.append(result)

            if result.success and result.stdout.strip():
                state.final_status = "SUCCESS"
                state.log("Sandbox", "✅", f"Fix Successful (Attempt {attempt})",
                          f"Completed in {result.execution_time}s with live output!")
                state.total_time = round(time.perf_counter() - pipeline_start, 2)
                self._notify(on_step, state)
                return state
            else:
                error_reason = result.stderr if not result.success else "Output is still empty. Add print() statements."
                state.log("Sandbox", "⚠️", f"Attempt {attempt} Incomplete",
                          f"{'TIMEOUT' if result.timed_out else error_reason[:120]}")
                self._notify(on_step, state)

        # ─── ALL REPAIRS EXHAUSTED ─────────────────────────────
        state.final_status = "SUCCESS" if (result.success and result.stdout.strip()) else "FAILED"
        state.log("Orchestrator", "🏁", "Pipeline Finished",
                  f"Total time: {round(time.perf_counter() - pipeline_start, 2)}s")
        state.total_time = round(time.perf_counter() - pipeline_start, 2)
        self._notify(on_step, state)
        return state

    def _notify(self, callback, state):
        """Fires the step callback if provided."""
        if callback:
            callback(state)
