from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


# Global
class State(str, Enum):
    PLAN = "plan"
    BROWSE = "browse"
    COMPLETED = "completed"


class Task(BaseModel):
    id: int
    description: str
    url: Optional[str]
    result: Optional[str]


class Memory(BaseModel):
    objective: str
    current_state: State
    plan: Optional[List[Task]]
    completed_tasks: Optional[List[Task]]
    current_task: Optional[List[Task]]
    final_response: Optional[str]

    class Config:
        use_enum_values = True


# Planner
class PlannerInput(BaseModel):
    objective: str
    plan: Optional[List[Task]]
    completed_tasks: Optional[List[Task]]
    task_for_review: Optional[Task]


class PlannerOutput(BaseModel):
    plan: Optional[List[Task]]
    next_task: Optional[Task]
    is_complete: bool
    final_response: Optional[str]


# Executor
class BrowserNavInput(BaseModel):
    task: Task


class BrowserNavOutput(BaseModel):
    completed_task: Task
