"""
FastAPI server using openenv.core base classes — required for validator.
"""
import random
from typing import Optional
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from sql_env.models import SQLAction, SQLObservation, SQLState
    from sql_env.tasks import TASK_SETS
    from sql_env.grader import grade, generate_feedback
except ImportError:
    from models import SQLAction, SQLObservation, SQLState
    from tasks import TASK_SETS
    from grader import grade, generate_feedback


class SQLCorrectionEnvironment(Environment):

    def __init__(self):
        super().__init__()
        self._difficulty = "easy"
        self._current_task = None
        self._step_count = 0
        self._done = False
        self._last_reward = 0.0
        self._rewards_history = []

    def reset(self, difficulty: str = "easy", task_id: str = None, **kwargs) -> SQLObservation:
        # task_id and difficulty are the same thing in our env
        actual_difficulty = task_id or difficulty or "easy"
        self._difficulty = actual_difficulty
        tasks = TASK_SETS.get(actual_difficulty, TASK_SETS["easy"])
        self._current_task = random.choice(tasks)
        self._step_count = 0
        self._done = False
        self._last_reward = 0.0
        self._rewards_history = []
        return SQLObservation(
            task_id=self._current_task.task_id,
            broken_query=self._current_task.broken_query,
            schema_context=self._current_task.schema_context,
            error_hint=self._current_task.error_hint,
            step_number=0,
            previous_attempt=None,
            feedback=None,
            reward=0.001,
            done=False,
        )
    
    def step(self, action: SQLAction) -> SQLObservation:
        self._step_count += 1
        reward_obj = grade(action, self._current_task)
        reward = reward_obj.value
        self._last_reward = reward
        self._rewards_history.append(reward)
        done = (reward >= 0.95) or (self._step_count >= self._current_task.max_steps)
        self._done = done
        feedback = generate_feedback(action, self._current_task, reward_obj)
        return SQLObservation(
            task_id=self._current_task.task_id,
            broken_query=self._current_task.broken_query,
            schema_context=self._current_task.schema_context,
            error_hint=self._current_task.error_hint,
            step_number=self._step_count,
            previous_attempt=action.corrected_query,
            feedback=feedback,
            reward=reward,
            done=done,
        )

    @property
    def state(self) -> SQLState:
        if self._current_task is None:
            return SQLState(
                task_id="none",
                difficulty="none",
                step_count=0,
                max_steps=0,
                done=False,
                last_reward=0.001,
                rewards_history=[],
            )
        return SQLState(
            task_id=self._current_task.task_id,
            difficulty=self._difficulty,
            step_count=self._step_count,
            max_steps=self._current_task.max_steps,
            done=self._done,
            last_reward=self._last_reward,
            rewards_history=self._rewards_history,
        )

app = create_app(
    SQLCorrectionEnvironment,
    SQLAction,
    SQLObservation,
    env_name="sql-correction-env",
    max_concurrent_envs=1,
)


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
from fastapi import Request

@app.get("/tasks")
async def list_tasks():
    return {
        "tasks": [
            {"id": "easy", "difficulty": "easy", "description": "Fix a single syntax error.", "steps": 5, "ideal_action": "correct_sql", "has_grader": True, "grader": "sql_env.grader.grade"},
            {"id": "medium", "difficulty": "medium", "description": "Fix multiple errors.", "steps": 5, "ideal_action": "correct_sql", "has_grader": True, "grader": "sql_env.grader.grade"},
            {"id": "hard", "difficulty": "hard", "description": "Fix complex multi-join queries.", "steps": 4, "ideal_action": "correct_sql", "has_grader": True, "grader": "sql_env.grader.grade"},
        ]
    }
