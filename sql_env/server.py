"""
FastAPI server using openenv.core base classes — required for validator.
"""
import random
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.interfaces import Environment

try:
    from sql_env.models import SQLAction, SQLObservation, SQLState
    from sql_env.tasks import TASK_SETS
    from sql_env.grader import grade, generate_feedback
except ImportError:
    from models import SQLAction, SQLObservation, SQLState
    from tasks import TASK_SETS
    from grader import grade, generate_feedback


class SQLCorrectionEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._difficulty = "easy"
        self._current_task = None
        self._step_count = 0
        self._done = False
        self._last_reward = 0.0
        self._rewards_history = []
        self._stagnation_count = 0

    def reset(self, seed=None, episode_id=None, **kwargs) -> SQLObservation:
        actual_difficulty = (
            kwargs.get("task_id")
            or kwargs.get("difficulty")
            or "easy"
        )
        self._difficulty = actual_difficulty
        tasks = TASK_SETS.get(actual_difficulty, TASK_SETS["easy"])
        self._current_task = random.choice(tasks)
        self._step_count = 0
        self._done = False
        self._last_reward = 0.0
        self._rewards_history = []
        self._stagnation_count = 0
        return self._make_observation(previous_attempt=None, feedback=None)

    def step(self, action: SQLAction) -> SQLObservation:
        if self._current_task is None:
            self.reset()

        self._step_count += 1
        reward_obj = grade(action, self._current_task)
        reward = reward_obj.value

        # Stagnation penalty: penalize repeating the same score
        if abs(reward - self._last_reward) < 0.01 and self._step_count > 1:
            self._stagnation_count += 1
            if self._stagnation_count >= 2:
                reward = max(0.0, reward - 0.1)
        else:
            self._stagnation_count = 0

        self._last_reward = reward
        self._rewards_history.append(reward)

        done = (reward_obj.value >= 0.95) or (
            self._step_count >= self._current_task.max_steps
        )
        self._done = done
        feedback = generate_feedback(action, self._current_task, reward_obj)

        return self._make_observation(
            previous_attempt=action.corrected_query,
            feedback=feedback,
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
                last_reward=0.0,
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

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _make_observation(
        self,
        previous_attempt: str | None,
        feedback: str | None,
    ) -> SQLObservation:
        assert self._current_task is not None
        max_steps = self._current_task.max_steps
        steps_remaining = max(0, max_steps - self._step_count)
        return SQLObservation(
            task_id=self._current_task.task_id,
            broken_query=self._current_task.broken_query,
            schema_context=self._current_task.schema_context,
            # Only surface the hint on easy tasks
            error_hint=(
                self._current_task.error_hint
                if self._difficulty == "easy"
                else None
            ),
            step_number=self._step_count,
            steps_remaining=steps_remaining,
            previous_attempt=previous_attempt,
            feedback=feedback,
        )


app = create_app(
    SQLCorrectionEnvironment,
    SQLAction,
    SQLObservation,
    env_name="sql-correction-env",
)


@app.get("/tasks")
async def list_tasks():
    """List available task difficulties with metadata."""
    return {
        "tasks": [
            {
                "id": "easy",
                "difficulty": "easy",
                "description": "Fix a single SQL keyword typo. Error hint provided.",
                "max_steps": 5,
                "count": 15,
            },
            {
                "id": "medium",
                "difficulty": "medium",
                "description": (
                    "Fix multiple errors across keywords and clauses. No hint."
                ),
                "max_steps": 5,
                "count": 15,
            },
            {
                "id": "hard",
                "difficulty": "hard",
                "description": (
                    "Fix complex multi-join queries including column name errors. "
                    "Schema provided, no hint."
                ),
                "max_steps": 4,
                "count": 10,
            },
        ]
    }


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
