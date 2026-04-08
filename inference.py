"""
inference.py — SQL Correction Environment Baseline Script
==========================================================
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

import httpx
from openai import OpenAI

# ── Environment variables ─────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
TASK_NAME    = os.getenv("SQL_ENV_TASK", "easy")
BENCHMARK    = "sql-correction-env"
ENV_URL = os.getenv("ENV_URL", "https://SyncShift-sql-correction-env.hf.space")
MAX_STEPS    = 8
SUCCESS_SCORE_THRESHOLD = 0.5

# ── Stdout loggers — DO NOT MODIFY FORMAT ────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float,
             done: bool, error: Optional[str]) -> None:
    err = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ").replace("\r", "").strip()
    print(
        f"[STEP] step={step} action={action_clean} "
        f"reward={reward:.2f} done={done_val} error={err}",
        flush=True,
    )

def log_end(success: bool, steps: int,
            score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert SQL debugger.
    You will be shown a broken SQL query that contains typos or keyword errors.
    Fix ALL errors and return ONLY the corrected SQL query.
    No explanation, no markdown, no code blocks, no backticks.
    Common errors: FORM->FROM, WEHRE->WHERE, GRUP->GROUP, HAVNG->HAVING,
    ORDR->ORDER, INNE->INNER, LFT->LEFT, BETWEN->BETWEEN, DSC->DESC, SELCT->SELECT.
""").strip()

# ── LLM call ──────────────────────────────────────────────────
def get_model_action(client: OpenAI, obs: dict, history: List[str]) -> str:
    history_block = "\n".join(history[-4:]) if history else "None"
    user_prompt = textwrap.dedent(f"""
        Broken SQL query:
        {obs['broken_query']}

        Schema context: {obs.get('schema_context') or 'Not provided'}
        Error hint: {obs.get('error_hint') or 'None'}
        Your previous attempt: {obs.get('previous_attempt') or 'None'}
        Feedback: {obs.get('feedback') or 'None'}

        Recent history:
        {history_block}

        Return ONLY the corrected SQL query.
    """).strip()

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
        return text if text else "SELECT 1"
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return "SELECT 1"

# ── Main episode loop ─────────────────────────────────────────
async def run_task(task_name: str) -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    rewards:     List[float] = []
    history:     List[str]   = []
    steps_taken: int         = 0
    score:       float       = 0.0
    success:     bool        = False

    log_start(task_name, BENCHMARK, MODEL_NAME)

    http = None
    try:
        http = httpx.AsyncClient(base_url=ENV_URL, timeout=60.0)

        try:
            reset_resp = await http.post("/reset", json={"task_name": task_name})
            reset_resp.raise_for_status()
            obs = reset_resp.json()
        except Exception as e:
            print(f"[DEBUG] Reset failed: {e}", flush=True)
            return

        for step in range(1, MAX_STEPS + 1):
            try:
                action_str = get_model_action(client, obs, history)
            except Exception as e:
                print(f"[DEBUG] Model failed: {e}", flush=True)
                action_str = "SELECT 1"

            try:
                step_resp = await http.post(
                    "/step",
                    json={"corrected_query": action_str},
                )
                step_resp.raise_for_status()
                result = step_resp.json()
            except Exception as e:
                print(f"[DEBUG] Step failed: {e}", flush=True)
                break

            obs         = result["observation"]
            reward      = float(result["reward"])
            done        = bool(result["done"])
            error       = result.get("info", {}).get("error")

            rewards.append(reward)
            steps_taken = step
            history.append(
                f"Step {step}: attempt={action_str!r} reward={reward:+.2f}"
            )

            log_step(step, action_str, reward, done, error)

            if done:
                break

        score   = min(max(sum(rewards) / len(rewards) if rewards else 0.0, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)

    finally:
        if http is not None:
            try:
                await http.aclose()
            except Exception as e:
                print(f"[DEBUG] HTTP close error: {e}", flush=True)
        log_end(success, steps_taken, score, rewards)

async def main() -> None:
    try:
        for difficulty in ("easy", "medium", "hard"):
            await run_task(difficulty)
            print("", flush=True)
    except Exception as e:
        print(f"[DEBUG] Main error: {e}", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[DEBUG] Fatal error: {e}", flush=True)
finally:
        sys.exit(0)