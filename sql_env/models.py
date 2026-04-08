from pydantic import BaseModel, Field
from typing import Optional, Any, Dict


class SQLObservation(BaseModel):
    task_id: str
    broken_query: str
    schema_context: Optional[str] = None
    error_hint: Optional[str] = None
    step_number: int
    previous_attempt: Optional[str] = None
    feedback: Optional[str] = None


class SQLAction(BaseModel):
    corrected_query: str


class SQLReward(BaseModel):
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


class StepResult(BaseModel):
    observation: SQLObservation
    reward: float
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)
