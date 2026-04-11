from typing import List, Optional, Any, Dict
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


class SQLAction(Action):
    corrected_query: str


class SQLObservation(Observation):
    task_id: str
    broken_query: str
    schema_context: Optional[str] = None
    error_hint: Optional[str] = None
    step_number: int
    previous_attempt: Optional[str] = None
    feedback: Optional[str] = None
    reward: float = 0.0
    done: bool = False


class SQLState(State):
    task_id: str
    difficulty: str
    step_count: int
    max_steps: int
    done: bool
    last_reward: float
    rewards_history: List[float]