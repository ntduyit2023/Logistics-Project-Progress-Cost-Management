from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AIInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    simulation_run_id: int
    action_type: List[str]
    target_tasks: List[str]
    human_message: Optional[str]
    modifications: Optional[Dict[str, Any]]
    impact: Optional[Dict[str, Any]]
    risk: Optional[Dict[str, Any]]
    created_at: Optional[datetime]


class SimulationCreate(BaseModel):
    ai_weights: Dict = Field(default={"time": 50, "cost": 50})


class SimulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    ai_weights: Dict
    status: str
    results_summary: Optional[Dict]
    created_at: Optional[datetime]
    insights: List[AIInsightResponse] = Field(default_factory=list)
