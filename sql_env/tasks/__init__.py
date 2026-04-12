from sql_env.tasks.easy import EASY_TASKS
from sql_env.tasks.medium import MEDIUM_TASKS
from sql_env.tasks.hard import HARD_TASKS

ALL_TASKS = {
    "easy": EASY_TASKS,
    "medium": MEDIUM_TASKS,
    "hard": HARD_TASKS,
}

# Alias used by server.py
TASK_SETS = ALL_TASKS

__all__ = ["ALL_TASKS", "TASK_SETS", "EASY_TASKS", "MEDIUM_TASKS", "HARD_TASKS"]
