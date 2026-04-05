import random
from typing import Optional
from sql_env.models import (
    SQLObservation, SQLAction, SQLTask, StepResult
)
from sql_env.grader import grade, generate_feedback
from sql_env.tasks import ALL_TASKS


class SQLCorrectionEnv:
    """
    OpenEnv-compliant SQL Query Correction Environment.

    The agent receives a broken SQL query and must return the corrected version.
    Reward is shaped across the full trajectory — partial credit is given for
    incremental improvements, penalizing stagnation and infinite loops.
    """

    def __init__(self, difficulty: str = "easy", task_index: Optional[int] = None):
        if difficulty not in ALL_TASKS:
            raise ValueError(f"difficulty must be one of {list(ALL_TASKS.keys())}")

        self.difficulty = difficulty
        self.task_index = task_index
        self._task: Optional[SQLTask] = None
        self._step_count: int = 0
        self._done: bool = False
        self._previous_attempt: Optional[str] = None
        self._last_feedback: Optional[str] = None
        self._last_reward: float = 0.0
        self._stagnation_count: int = 0

    # ── OpenEnv Interface ─────────────────────────────────────

    async def reset(self) -> SQLObservation:
        """Reset the environment and return the initial observation."""
        tasks = ALL_TASKS[self.difficulty]
        if self.task_index is not None:
            self._task = tasks[self.task_index % len(tasks)]
        else:
            self._task = random.choice(tasks)

        self._step_count = 0
        self._done = False
        self._previous_attempt = None
        self._last_feedback = None
        self._last_reward = 0.0
        self._stagnation_count = 0

        return self._make_observation()

    async def step(self, action: SQLAction) -> StepResult:
        """
        Take one step: grade the agent's corrected query and return
        (observation, reward, done, info).
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")
        if self._task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        self._step_count += 1

        # grade the action
        reward_model = grade(action, self._task)
        reward = reward_model.value

        # detect stagnation (same reward twice in a row) — penalize
        if abs(reward - self._last_reward) < 0.01 and self._step_count > 1:
            self._stagnation_count += 1
            if self._stagnation_count >= 2:
                reward = max(0.0, reward - 0.1)  # stagnation penalty
        else:
            self._stagnation_count = 0

        self._last_reward = reward

        # generate feedback for the next observation
        feedback = generate_feedback(action, self._task, reward_model)
        self._last_feedback = feedback
        self._previous_attempt = action.corrected_query

        # episode ends on perfect score or max steps reached
        done = reward_model.value == 1.0 or self._step_count >= self._task.max_steps
        self._done = done

        obs = self._make_observation()

        return StepResult(
            observation=obs,
            reward=round(reward, 4),
            done=done,
            info={
                "grader_reason": reward_model.reason,
                "step": self._step_count,
                "max_steps": self._task.max_steps,
                "task_id": self._task.task_id,
            }
        )

    async def state(self) -> dict:
        """Return the current internal state of the environment."""
        if self._task is None:
            return {"status": "not_initialized"}
        return {
            "task_id": self._task.task_id,
            "difficulty": self.difficulty,
            "step_count": self._step_count,
            "done": self._done,
            "last_reward": self._last_reward,
            "max_steps": self._task.max_steps,
            "previous_attempt": self._previous_attempt,
        }

    async def close(self):
        """Clean up resources."""
        self._task = None
        self._done = True

    # ── Internal ──────────────────────────────────────────────

    def _make_observation(self) -> SQLObservation:
        assert self._task is not None
        return SQLObservation(
            task_id=self._task.task_id,
            broken_query=self._task.broken_query,
            schema_context=self._task.schema_context,
            error_hint=self._task.error_hint if self.difficulty == "easy" else None,
            step_number=self._step_count,
            previous_attempt=self._previous_attempt,
            feedback=self._last_feedback,
        )
