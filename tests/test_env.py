"""
tests/test_env.py — Smoke tests and grader unit tests.

Run with:  pytest tests/ -v
"""
import asyncio
import pytest
from sql_env.models import SQLAction, SQLTask
from sql_env.grader import grade, generate_feedback
from sql_env.env import SQLCorrectionEnv
from sql_env.tasks import ALL_TASKS, EASY_TASKS, MEDIUM_TASKS, HARD_TASKS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_task(broken: str, canonical: str, difficulty: str = "easy") -> SQLTask:
    return SQLTask(
        task_id="test_task",
        difficulty=difficulty,
        broken_query=broken,
        canonical_answer=canonical,
    )


def _action(query: str) -> SQLAction:
    return SQLAction(corrected_query=query)


# ── Grader unit tests ─────────────────────────────────────────────────────────

class TestGrader:
    def test_exact_match_returns_one(self):
        task = _make_task(
            "SELECT * FORM users",
            "SELECT * FROM users",
        )
        reward = grade(_action("SELECT * FROM users"), task)
        assert reward.value == 1.0

    def test_exact_match_case_insensitive(self):
        task = _make_task(
            "SELECT * FORM users",
            "SELECT * FROM users",
        )
        reward = grade(_action("select * from users"), task)
        assert reward.value == 1.0

    def test_exact_match_trailing_semicolon(self):
        task = _make_task(
            "SELECT * FORM users",
            "SELECT * FROM users",
        )
        reward = grade(_action("SELECT * FROM users;"), task)
        assert reward.value == 1.0

    def test_wrong_answer_not_one(self):
        task = _make_task(
            "SELECT * FORM users",
            "SELECT * FROM users",
        )
        reward = grade(_action("SELECT * FORM users"), task)
        assert reward.value < 1.0

    def test_completely_wrong_returns_zero(self):
        task = _make_task(
            "SELECT * FORM users",
            "SELECT * FROM users",
        )
        reward = grade(_action("hello world"), task)
        assert reward.value == 0.0

    def test_basic_structure_returns_02(self):
        task = _make_task(
            "SELECT * FORM users WHERE id = 1",
            "SELECT * FROM users WHERE id = 1",
        )
        # Correct structure, still has FROM typo
        reward = grade(_action("SELECT * FORM users WHERE id = 1"), task)
        assert reward.value == pytest.approx(0.2, abs=0.05)

    def test_reward_range(self):
        task = _make_task(
            "SELCT * FORM users WEHRE id = 1",
            "SELECT * FROM users WHERE id = 1",
        )
        for query in [
            "hello world",
            "SELECT * FORM users",
            "SELECT * FROM users WHERE id = 1",
            "select * from users where id = 1",
        ]:
            reward = grade(_action(query), task)
            assert 0.0 <= reward.value <= 1.0, (
                f"Reward {reward.value} out of [0, 1] for query: {query}"
            )

    def test_feedback_not_empty(self):
        task = _make_task("SELECT * FORM users", "SELECT * FROM users")
        reward = grade(_action("SELECT * FROM users"), task)
        fb = generate_feedback(_action("SELECT * FROM users"), task, reward)
        assert isinstance(fb, str) and len(fb) > 0


# ── Task catalogue tests ──────────────────────────────────────────────────────

class TestTaskCatalogue:
    def test_easy_task_count(self):
        assert len(EASY_TASKS) >= 10, "Need at least 10 easy tasks"

    def test_medium_task_count(self):
        assert len(MEDIUM_TASKS) >= 10, "Need at least 10 medium tasks"

    def test_hard_task_count(self):
        assert len(HARD_TASKS) >= 5, "Need at least 5 hard tasks"

    def test_all_task_ids_unique(self):
        all_ids = [t.task_id for tasks in ALL_TASKS.values() for t in tasks]
        assert len(all_ids) == len(set(all_ids)), "Duplicate task IDs found"

    def test_easy_tasks_have_hints(self):
        for task in EASY_TASKS:
            assert task.error_hint is not None and len(task.error_hint) > 0, (
                f"Easy task {task.task_id} missing error_hint"
            )

    def test_hard_tasks_have_schema(self):
        for task in HARD_TASKS:
            assert task.schema_context is not None and len(task.schema_context) > 0, (
                f"Hard task {task.task_id} missing schema_context"
            )

    def test_canonical_answers_are_valid_sql(self):
        """Canonical answers must at least contain SELECT and FROM."""
        for difficulty, tasks in ALL_TASKS.items():
            for task in tasks:
                upper = task.canonical_answer.upper()
                assert "SELECT" in upper, (
                    f"{task.task_id}: canonical_answer missing SELECT"
                )
                assert "FROM" in upper, (
                    f"{task.task_id}: canonical_answer missing FROM"
                )

    def test_grading_canonical_answer_returns_perfect(self):
        """Every task must return 1.0 when given its own canonical answer."""
        for difficulty, tasks in ALL_TASKS.items():
            for task in tasks:
                action = _action(task.canonical_answer)
                reward = grade(action, task)
                assert reward.value == 1.0, (
                    f"{task.task_id}: canonical answer did not score 1.0 "
                    f"(got {reward.value})"
                )

    def test_grading_broken_query_below_perfect(self):
        """Broken queries must score below 1.0."""
        for difficulty, tasks in ALL_TASKS.items():
            for task in tasks:
                action = _action(task.broken_query)
                reward = grade(action, task)
                assert reward.value < 1.0, (
                    f"{task.task_id}: broken query unexpectedly scored 1.0"
                )


# ── Environment integration tests ─────────────────────────────────────────────

class TestEnvironment:
    def test_reset_returns_observation(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="easy")
            obs = await env.reset()
            assert obs.task_id is not None
            assert obs.broken_query is not None
            assert obs.step_number == 0
            assert obs.steps_remaining == 5

        asyncio.run(run())

    def test_step_returns_result(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="easy")
            await env.reset()
            result = await env.step(_action("SELECT * FROM users WHERE id = 1"))
            assert 0.0 <= result.reward <= 1.0
            assert isinstance(result.done, bool)
            assert result.observation.step_number == 1

        asyncio.run(run())

    def test_steps_remaining_decrements(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="easy")
            await env.reset()
            result = await env.step(_action("SELECT * FROM x"))
            assert result.observation.steps_remaining == 4

        asyncio.run(run())

    def test_correct_answer_terminates(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="easy", task_index=0)
            await env.reset()
            canonical = EASY_TASKS[0].canonical_answer
            result = await env.step(_action(canonical))
            assert result.done is True
            assert result.reward == pytest.approx(1.0)

        asyncio.run(run())

    def test_max_steps_terminates(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="easy", task_index=0)
            await env.reset()
            result = None
            for _ in range(5):
                result = await env.step(_action("SELECT * FORM users"))
            assert result.done is True

        asyncio.run(run())

    def test_done_episode_raises(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="easy", task_index=0)
            await env.reset()
            canonical = EASY_TASKS[0].canonical_answer
            await env.step(_action(canonical))  # this terminates
            with pytest.raises(RuntimeError):
                await env.step(_action("SELECT 1"))

        asyncio.run(run())

    def test_medium_hint_hidden(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="medium")
            obs = await env.reset()
            assert obs.error_hint is None

        asyncio.run(run())

    def test_hard_schema_present(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="hard")
            obs = await env.reset()
            assert obs.schema_context is not None

        asyncio.run(run())

    def test_state_reflects_progress(self):
        async def run():
            env = SQLCorrectionEnv(difficulty="easy", task_index=0)
            await env.reset()
            await env.step(_action("SELECT * FORM users"))
            state = await env.state()
            assert state["step_count"] == 1
            assert state["done"] is False

        asyncio.run(run())

    def test_all_difficulties_reset(self):
        async def run():
            for diff in ["easy", "medium", "hard"]:
                env = SQLCorrectionEnv(difficulty=diff)
                obs = await env.reset()
                assert obs.broken_query is not None

        asyncio.run(run())
