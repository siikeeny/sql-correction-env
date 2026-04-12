from typing import List, Optional, Any
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field, BaseModel


class SQLAction(Action):
    corrected_query: str


class SQLObservation(Observation):
    """
    Observation returned to the agent each step.

    Fields:
        task_id:          Unique identifier for the current task instance.
        broken_query:     The malformed SQL query the agent must fix.
        schema_context:   Table/column definitions (hard tasks only).
        error_hint:       Plain-language hint about the error (easy tasks only).
        step_number:      Current step within the episode (0 = initial observation).
        steps_remaining:  How many steps are left before the episode ends.
        previous_attempt: The agent's SQL output from the previous step.
        feedback:         Grader feedback on the previous attempt.
    """
    task_id: str
    broken_query: str
    schema_context: Optional[str] = None
    error_hint: Optional[str] = None
    step_number: int
    steps_remaining: Optional[int] = None
    previous_attempt: Optional[str] = None
    feedback: Optional[str] = None


class SQLState(State):
    task_id: str
    difficulty: str
    step_count: int
    max_steps: int
    done: bool
    last_reward: float
    rewards_history: List[float]


class SQLReward(BaseModel):
    # Allow full [0.0, 1.0] range so perfect matches can return exactly 1.0
    value: float = Field(ge=0.0, le=1.0)
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
