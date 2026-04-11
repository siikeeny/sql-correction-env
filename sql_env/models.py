from typing import List, Optional, Any, Callable
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field, BaseModel


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


class SQLReward(BaseModel):
    value: float = Field(gt=0.0, lt=1.0)
    reason: str


class SQLTask(BaseModel):
    task_id: str
    difficulty: str
    broken_query: str
    canonical_answer: str
    schema_context: Optional[str] = None
    error_hint: Optional[str] = None
    max_steps: int = 5
    grader: Optional[Any] = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}


class StepResult(BaseModel):
    observation: SQLObservation
    reward: float
    done: bool
    info: dict = Field(default_factory=dict)