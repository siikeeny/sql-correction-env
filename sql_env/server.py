"""
FastAPI HTTP wrapper for SQLCorrectionEnv.

Exposes the OpenEnv-required endpoints: /reset, /step, /state + /tasks for validator.
"""

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openenv.core.env_server import Environment
from sql_env import SQLAction, SQLCorrectionEnv
from sql_env.tasks import ALL_TASKS


class ResetRequest(BaseModel):
    difficulty: Optional[str] = "easy"
    task_name: Optional[str] = None
    task_index: Optional[int] = None


class StepRequest(BaseModel):
    corrected_query: str


env: Optional[SQLCorrectionEnv] = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global env
    env = SQLCorrectionEnv(difficulty="easy")
    yield
    if env is not None:
        await env.close()


app = FastAPI(
    title="SQL Correction RL Environment",
    description="OpenEnv-compliant environment for SQL query correction tasks.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()):
    """Reset the environment and return the initial observation."""
    global env
    difficulty = request.task_name or request.difficulty or "easy"
    if difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(status_code=400, detail="difficulty must be easy, medium, or hard")

    env = SQLCorrectionEnv(
        difficulty=difficulty,
        task_index=request.task_index,
    )
    obs = await env.reset()
    return obs.model_dump()


@app.post("/step")
async def step(request: StepRequest):
    """Take one step and return the new observation, reward, done flag, and info."""
    global env
    if env is None:
        raise HTTPException(status_code=400, detail="Call /reset first.")

    try:
        action = SQLAction(corrected_query=request.corrected_query)
        result = await env.step(action)
        return result.model_dump()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/state")
async def state():
    """Return current environment state."""
    global env
    if env is None:
        return {"status": "not_initialized"}
    return await env.state()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sql-correction-env"}


@app.get("/tasks")
async def list_tasks():
    """Return graded tasks in openenv validator format."""
    from sql_env.grader import grade
    return {
        "tasks": [
            {
                "name": "easy",
                "difficulty": "easy",
                "description": "Fix a single syntax error. Error hint provided.",
                "max_steps": 5,
                "has_grader": True,
                "grader": "sql_env.grader.grade",
                "grader_fn": grade.__module__ + "." + grade.__qualname__,
            },
            {
                "name": "medium",
                "difficulty": "medium",
                "description": "Fix multiple errors. No hint.",
                "max_steps": 5,
                "has_grader": True,
                "grader": "sql_env.grader.grade",
                "grader_fn": grade.__module__ + "." + grade.__qualname__,
            },
            {
                "name": "hard",
                "difficulty": "hard",
                "description": "Fix complex multi-join queries. Schema provided.",
                "max_steps": 4,
                "has_grader": True,
                "grader": "sql_env.grader.grade",
                "grader_fn": grade.__module__ + "." + grade.__qualname__,
            },
        ]
    }


@app.get("/")
async def root():
    return {
        "name": "SQL Correction RL Environment",
        "version": "1.0.0",
        "endpoints": ["/reset", "/step", "/state", "/health", "/tasks"],
        "tasks": ["easy", "medium", "hard"],
    }


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()