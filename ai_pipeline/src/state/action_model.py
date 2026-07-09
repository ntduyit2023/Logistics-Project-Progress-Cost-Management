"""
Action Model Module for Dynamic Project State Evolution
========================================================
GLPO - Graph Logistics Project Optimization

Defines ActionType and ActionObject structures representing actions
applied to tasks and graph dependencies (Crash, Outsource, Fast Tracking, Resource Leveling).
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

class ActionType(Enum):
    NORMAL = "Normal"
    CRASH = "Crash"
    OUTSOURCE = "Outsource"
    FAST_TRACKING = "FastTracking"
    RESOURCE_LEVELING = "ResourceLeveling"

    @classmethod
    def from_string(cls, val: str) -> 'ActionType':
        mapping = {
            "normal": cls.NORMAL,
            "crash": cls.CRASH,
            "outsource": cls.OUTSOURCE,
            "fasttracking": cls.FAST_TRACKING,
            "fast_tracking": cls.FAST_TRACKING,
            "resourceleveling": cls.RESOURCE_LEVELING,
            "resource_leveling": cls.RESOURCE_LEVELING,
        }
        return mapping.get(str(val).lower().replace(" ", "_"), cls.NORMAL)

@dataclass
class ActionObject:
    action_type: ActionType
    affected_tasks: List[str]
    priority: int = 1
    overlap_ratio: float = 0.3          # For Fast Tracking (lead time ratio, e.g. 0.3 = 30% overlap)
    crash_level: float = 1.5            # For Crashing (duration divisor, e.g. 1.5x speed)
    outsource_level: float = 2.0        # For Outsource (duration divisor, e.g. 2.0x speed)
    resource_delta: Dict[str, float] = field(default_factory=dict)
    expected_duration_delta: float = 0.0
    expected_cost_delta: float = 0.0
    expected_risk_delta: float = 0.0
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "affected_tasks": list(self.affected_tasks),
            "priority": self.priority,
            "overlap_ratio": float(self.overlap_ratio),
            "crash_level": float(self.crash_level),
            "outsource_level": float(self.outsource_level),
            "resource_delta": dict(self.resource_delta),
            "expected_duration_delta": float(self.expected_duration_delta),
            "expected_cost_delta": float(self.expected_cost_delta),
            "expected_risk_delta": float(self.expected_risk_delta),
            "custom_params": dict(self.custom_params)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionObject':
        action_type = ActionType.from_string(data.get("action_type", "Normal"))
        return cls(
            action_type=action_type,
            affected_tasks=list(data.get("affected_tasks", [])),
            priority=int(data.get("priority", 1)),
            overlap_ratio=float(data.get("overlap_ratio", 0.3)),
            crash_level=float(data.get("crash_level", 1.5)),
            outsource_level=float(data.get("outsource_level", 2.0)),
            resource_delta=dict(data.get("resource_delta", {})),
            expected_duration_delta=float(data.get("expected_duration_delta", 0.0)),
            expected_cost_delta=float(data.get("expected_cost_delta", 0.0)),
            expected_risk_delta=float(data.get("expected_risk_delta", 0.0)),
            custom_params=dict(data.get("custom_params", {}))
        )

    @classmethod
    def from_pareto_option(cls, option_solution: Dict[str, Any], tasks: List[Dict[str, Any]]) -> 'ActionObject':
        """
        Converts an NSGA-II solution / Pareto option into an ActionObject.
        Option solution contains 'modes' list corresponding to tasks.
        Mode 0: Normal, Mode 1: Crash, Mode 2: Outsource
        """
        modes = option_solution.get("modes", [])
        crashed = []
        outsourced = []
        
        for idx, mode in enumerate(modes):
            if idx < len(tasks):
                t_id = str(tasks[idx]['id'])
                if mode == 1:
                    crashed.append(t_id)
                elif mode == 2:
                    outsourced.append(t_id)

        # Determine dominant action type
        if len(crashed) >= len(outsourced) and len(crashed) > 0:
            act_type = ActionType.CRASH
            affected = crashed
        elif len(outsourced) > 0:
            act_type = ActionType.OUTSOURCE
            affected = outsourced
        else:
            act_type = ActionType.NORMAL
            affected = []

        return cls(
            action_type=act_type,
            affected_tasks=affected,
            priority=1,
            crash_level=1.5,
            outsource_level=2.0,
            expected_duration_delta=float(option_solution.get("makespan", 0.0)),
            expected_cost_delta=float(option_solution.get("cost", 0.0)),
            expected_risk_delta=float(option_solution.get("risk", 0.0)),
            custom_params={"modes": list(modes)}
        )
