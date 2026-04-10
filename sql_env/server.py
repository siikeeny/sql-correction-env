"""
FastAPI HTTP wrapper for SQLCorrectionEnv using openenv.core base classes.
"""
from openenv.core.env_server import create_fastapi_app
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from sql_env.models import SQLAction, SQLObservation
from sql_env.tasks import ALL_TASKS, TASK_SETS
from sql_env.grader import grade, generate_feedback
import random


class SQLCorrectionEnvironment(Environment):

    def __init__(self):
        super().__init__()
        self._difficulty = "easy"
        self._current_task = None
        self._step_count = 0
        self._done = False
        self._last_reward = 0.0
        self._previous_attempt = None
        self._feedback = None
        self._rewards_history = []

    def reset(self, difficulty: str = "easy") -> SQLObservation:
        self._difficulty = difficulty
        tasks = TASK_SETS.get(difficulty, TASK_SETS["easy"])
        self._current_task = random.choice(tasks)
        self._step_count = 0
        self._done = False
        self._last_reward = 0.0
        self._previous_attempt = None
        self._feedback = None
        self._rewards_history = []
        return SQLObservation(
            task_id=self._current_task.task_id,
            broken_query=self._current_task.broken_query,
            schema_context=self._current_task.schema_context,
            error_hint=self._current_task.error_hint,
            step_number=0,
            previous_attempt=None,
            feedback=None,
        )

    def step(self, action: SQLAction) -> SQLObservation:
        self._step_count += 1
        reward_obj = grade(action, self._current_task)
        reward = reward_obj.value
        self._last_reward = reward
        self._previous_attempt = action.corrected_query
        self._feedback = generate_feedback(action, self._current_task, reward_obj)
        self._rewards_history.append(reward)
        done = (reward >= 0.95) or (self._step_count >= self._current_task.max_steps)
        self._done = done
        return SQLObservation(
            task_id=self._current_task.task_id,
            broken_query=self._current_task.broken_query,
            schema_context=self._current_task.schema_context,
            error_hint=self._current_task.error_hint,
            step_number=self._step_count,
            previous_attempt=self._previous_attempt,
            feedback=self._feedback,
        )

    @property
    def state(self) -> dict:
        if self._current_task is None:
            return {"status": "not_initialized"}
        return {
            "task_id": self._current_task.task_id,
            "difficulty": self._difficulty,
            "step_count": self._step_count,
            "done": self._done,
            "last_reward": self._last_reward,
            "rewards_history": self._rewards_history,
        }

    def get_tasks(self):
        return {
            "tasks": [
                {
                    "name": "easy",
                    "difficulty": "easy",
                    "description": "Fix a single syntax error. Error hint provided.",
                    "max_steps": 5,
                    "has_grader": True,
                    "grader": "sql_env.grader.grade",
                },
                {
                    "name": "medium",
                    "difficulty": "medium",
                    "description": "Fix multiple errors. No hint.",
                    "max_steps": 5,
                    "has_grader": True,
                    "grader": "sql_env.grader.grade",
                },
                {
                    "name": "hard",
                    "difficulty": "hard",
                    "description": "Fix complex multi-join queries. Schema provided.",
                    "max_steps": 4,
                    "has_grader": True,
                    "grader": "sql_env.grader.grade",
                },
            ]
        }


env = SQLCorrectionEnvironment()
app = create_fastapi_app(env, SQLAction, SQLObservation)


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()