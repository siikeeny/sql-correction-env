"""
inference.py - SQL Correction Environment Baseline Script
=========================================================
MANDATORY - Place this file in the ROOT of the project.

Required environment variables:
  API_BASE_URL   The API endpoint for the LLM
  MODEL_NAME     The model identifier to use for inference
  HF_TOKEN       Your Hugging Face / API key
  ENV_URL        URL of the running environment (default: http://localhost:7860)
  SQL_ENV_TASK   Task difficulty: easy | medium | hard (default: easy)
"""

import asyncio
import os
import sys
import textwrap
from typing import List, Optional
import re

import httpx

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
TASK_NAME    = os.getenv("SQL_ENV_TASK", "easy")
BENCHMARK    = "sql-correction-env"
ENV_URL      = os.getenv("ENV_URL", "http://localhost:7860")
MAX_STEPS    = 8
SUCCESS_SCORE_THRESHOLD = 0.5


# ---------------------------------------------------------------------------
# Logging helpers — must match the spec format exactly
# ---------------------------------------------------------------------------

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int,
    action: str,
    reward: float,
    done: bool,
    error: Optional[str],
) -> None:
    err = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ").replace("\r", "").strip()
    print(
        f"[STEP] step={step} action={action_clean} "
        f"reward={reward:.2f} done={done_val} error={err}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else ""
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# LLM / heuristic helpers
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert SQL debugger.
    You will be shown a broken SQL query that contains typos or keyword errors.
    Fix ALL errors and return ONLY the corrected SQL query.
    No explanation, no markdown, no code blocks, no backticks.
    Common keyword typos to watch for:
      FORM->FROM, WEHRE->WHERE, WHER->WHERE,
      GRUP->GROUP, HAVNG->HAVING, ORDR->ORDER,
      INNE->INNER, LFT->LEFT, BETWEN->BETWEEN,
      DSC->DESC, SELCT->SELECT, LIMT->LIMIT.
    Also watch for column name errors described in the schema context.
    """
).strip()

SQL_REPLACEMENTS = {
    "FORM":   "FROM",
    "WEHRE":  "WHERE",
    "WHER":   "WHERE",
    "GRUP":   "GROUP",
    "HAVNG":  "HAVING",
    "ORDR":   "ORDER",
    "INNE":   "INNER",
    "LFT":    "LEFT",
    "BETWEN": "BETWEEN",
    "DSC":    "DESC",
    "SELCT":  "SELECT",
    "LIMT":   "LIMIT",
}


def heuristic_correct_sql(query: str) -> str:
    """Deterministic fallback when the LLM is unavailable."""
    corrected = query
    for broken, fixed in SQL_REPLACEMENTS.items():
        corrected = re.sub(
            rf"\b{re.escape(broken)}\b", fixed, corrected, flags=re.IGNORECASE
        )
    return corrected.strip()


def get_model_action(
    client: Optional["OpenAI"],
    obs: dict,
    history: List[str],
) -> str:
    """Return a corrected SQL string. Falls back to heuristic on any failure."""
    heuristic = heuristic_correct_sql(obs.get("broken_query", ""))

    if client is None:
        return heuristic

    history_block = "\n".join(history[-4:]) if history else "None"
    user_prompt = textwrap.dedent(
        f"""
        Broken SQL query:
        {obs.get("broken_query", "")}

        Schema context:    {obs.get("schema_context") or "Not provided"}
        Error hint:        {obs.get("error_hint") or "None"}
        Steps remaining:   {obs.get("steps_remaining", "?")}
        Previous attempt:  {obs.get("previous_attempt") or "None"}
        Feedback:          {obs.get("feedback") or "None"}

        Recent history:
        {history_block}

        Return ONLY the corrected SQL query.
        """
    ).strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=300,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text if text else heuristic
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return heuristic


# ---------------------------------------------------------------------------
# Episode runner
# ---------------------------------------------------------------------------

async def run_task(task_name: str) -> None:
    """
    Run one full episode for `task_name`.

    The [END] log line is ALWAYS emitted via the finally block, even if an
    exception occurs mid-episode or the reset call fails.
    """
    rewards: List[float] = []
    history: List[str]   = []
    steps_taken = 0
    score       = 0.0
    success     = False

    client = None
    if OpenAI is not None and API_KEY not in {"", "dummy"}:
        try:
            client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
        except Exception as exc:
            print(f"[DEBUG] OpenAI client init failed: {exc}", flush=True)

    log_start(task_name, BENCHMARK, MODEL_NAME)

    http: Optional[httpx.AsyncClient] = None
    try:
        http = httpx.AsyncClient(base_url=ENV_URL, timeout=60.0)

        # ── reset ──────────────────────────────────────────────────────────
        reset_failed = False
        obs: dict = {}
        try:
            reset_resp = await http.post(
                "/reset", json={"difficulty": task_name}
            )
            reset_resp.raise_for_status()
            reset_data = reset_resp.json()
            # The openenv wrapper may nest the observation under "observation"
            obs = reset_data.get("observation", reset_data)
        except Exception as exc:
            print(f"[DEBUG] Reset failed: {exc}", flush=True)
            reset_failed = True

        if not reset_failed:
            # ── step loop ──────────────────────────────────────────────────
            for step in range(1, MAX_STEPS + 1):
                try:
                    action_str = get_model_action(client, obs, history)
                except Exception as exc:
                    print(f"[DEBUG] Model action failed: {exc}", flush=True)
                    action_str = heuristic_correct_sql(
                        obs.get("broken_query", "")
                    )

                try:
                    # Action must be wrapped under {"action": {...}}
                    step_resp = await http.post(
                        "/step",
                        json={"action": {"corrected_query": action_str}},
                    )
                    step_resp.raise_for_status()
                    result = step_resp.json()
                except Exception as exc:
                    print(f"[DEBUG] Step {step} request failed: {exc}", flush=True)
                    rewards.append(0.0)
                    steps_taken = step
                    log_step(step, action_str, 0.0, True, str(exc))
                    break

                obs    = result.get("observation", obs)
                reward = float(result.get("reward", 0.0))
                done   = bool(result.get("done", False))
                info   = result.get("info")
                error  = info.get("error") if isinstance(info, dict) else None

                rewards.append(reward)
                steps_taken = step
                history.append(
                    f"Step {step}: attempt={action_str!r} reward={reward:+.2f}"
                )

                log_step(step, action_str, reward, done, error)

                if done:
                    break

            if rewards:
                score   = min(max(sum(rewards) / len(rewards), 0.01), 0.99)
            success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Unhandled episode error: {exc}", flush=True)

    finally:
        if http is not None:
            try:
                await http.aclose()
            except Exception as exc:
                print(f"[DEBUG] HTTP close error: {exc}", flush=True)
        log_end(success, steps_taken, score, rewards)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    """Run all three difficulties in sequence so validator sees 3 [END] lines."""
    try:
        for difficulty in ("easy", "medium", "hard"):
            await run_task(difficulty)
            print("", flush=True)
    except Exception as exc:
        print(f"[DEBUG] Main loop error: {exc}", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"[DEBUG] Fatal error: {exc}", flush=True)
    finally:
        sys.exit(0)
