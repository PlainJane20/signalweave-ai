"""Specialist agent registry."""

from northstar.agents.architecture import ArchitectureAgent
from northstar.agents.economics import EconomicsAgent
from northstar.agents.execution import ExecutionAgent
from northstar.agents.governance import GovernanceAgent
from northstar.agents.premortem import PremortemAgent
from northstar.agents.strategy import StrategyAgent

__all__ = [
    "ArchitectureAgent",
    "EconomicsAgent",
    "ExecutionAgent",
    "GovernanceAgent",
    "PremortemAgent",
    "StrategyAgent",
]
