"""Strict, provider-neutral contracts shared by every Northstar component."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def score(self) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]


class FindingCategory(str, Enum):
    STRATEGY = "strategy_alignment"
    BREAKING_API = "breaking_api"
    SPOF = "single_point_of_failure"
    DEPENDENCY = "cross_team_dependency"
    CAPACITY = "capacity"
    OWNERSHIP = "ownership"
    PRIVACY = "privacy"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    ECONOMICS = "portfolio_economics"
    PREMORTEM = "premortem"


class GateStatus(str, Enum):
    ALLOW = "allow"
    HUMAN_REVIEW = "human_review"
    BLOCK = "block"


class Objective(StrictModel):
    id: Annotated[str, Field(pattern=r"^OBJ-[A-Z0-9-]+$")]
    name: str = Field(min_length=3, max_length=160)
    weight: float = Field(ge=0, le=1)
    target_metric: str = Field(min_length=3, max_length=200)


class Team(StrictModel):
    id: Annotated[str, Field(pattern=r"^TEAM-[A-Z0-9-]+$")]
    name: str
    available_engineers: int = Field(ge=0, le=10_000)
    quarterly_capacity_points: int = Field(gt=0, le=100_000)


class Initiative(StrictModel):
    id: Annotated[str, Field(pattern=r"^INIT-[A-Z0-9-]+$")]
    name: str
    owner_team_id: Optional[str] = None
    objective_ids: list[str] = Field(default_factory=list)
    dependency_ids: list[str] = Field(default_factory=list)
    required_capacity_points: int = Field(ge=0)
    required_engineers: int = Field(ge=0)
    annual_cost_usd: int = Field(ge=0)
    expected_annual_value_usd: int = Field(ge=0)
    strategic_value: float = Field(ge=0, le=100)
    delivery_confidence: float = Field(ge=0, le=1)
    target_quarter: int = Field(ge=1, le=12)
    alternative_vendor_cost_usd: Optional[int] = Field(default=None, ge=0)
    systems: list[str] = Field(default_factory=list)


class Service(StrictModel):
    id: Annotated[str, Field(pattern=r"^SVC-[A-Z0-9-]+$")]
    name: str
    replicas: int = Field(ge=0)
    recovery_time_minutes: int = Field(ge=0)
    contains_phi: bool = False
    encryption_at_rest: bool = True
    audit_logging: bool = True


class ApiChange(StrictModel):
    id: Annotated[str, Field(pattern=r"^API-[A-Z0-9-]+$")]
    service_id: str
    consumer_team_ids: list[str] = Field(default_factory=list)
    backward_compatible: bool
    compatibility_window_days: int = Field(ge=0)


class ProgramScenario(StrictModel):
    id: Annotated[str, Field(pattern=r"^SCN-[A-Z0-9-]+$")]
    title: str
    organization: str
    synthetic_data: bool = True
    external_processing_allowed: bool = False
    objectives: list[Objective]
    teams: list[Team]
    initiatives: list[Initiative]
    services: list[Service] = Field(default_factory=list)
    api_changes: list[ApiChange] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> "ProgramScenario":
        objective_ids = {item.id for item in self.objectives}
        team_ids = {item.id for item in self.teams}
        initiative_ids = {item.id for item in self.initiatives}
        service_ids = {item.id for item in self.services}
        errors: list[str] = []
        for initiative in self.initiatives:
            if initiative.owner_team_id and initiative.owner_team_id not in team_ids:
                errors.append(f"{initiative.id} references unknown team {initiative.owner_team_id}")
            errors.extend(
                f"{initiative.id} references unknown objective {ref}"
                for ref in initiative.objective_ids if ref not in objective_ids
            )
            errors.extend(
                f"{initiative.id} references unknown dependency {ref}"
                for ref in initiative.dependency_ids if ref not in initiative_ids
            )
        for change in self.api_changes:
            if change.service_id not in service_ids:
                errors.append(f"{change.id} references unknown service {change.service_id}")
            errors.extend(
                f"{change.id} references unknown consumer team {ref}"
                for ref in change.consumer_team_ids if ref not in team_ids
            )
        if errors:
            raise ValueError("; ".join(errors))
        return self


class Evidence(StrictModel):
    source_id: str
    statement: str = Field(min_length=5)
    metric_value: Optional[float] = None
    metric_unit: Optional[str] = None


class Finding(StrictModel):
    id: Annotated[str, Field(pattern=r"^[A-Z]+-[A-Z0-9-]+$")]
    agent: str
    category: FindingCategory
    severity: Severity
    title: str
    affected_initiative_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(min_length=1)
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    requires_human_decision: bool = False


class AgentAssessment(StrictModel):
    agent: str
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    analysis_mode: Literal["offline", "openai"] = "offline"


class PolicyConfig(StrictModel):
    blocked_categories: set[FindingCategory] = Field(
        default_factory=lambda: {
            FindingCategory.PRIVACY,
            FindingCategory.SECURITY,
            FindingCategory.COMPLIANCE,
        }
    )
    block_at_or_above: Severity = Severity.CRITICAL
    review_at_or_above: Severity = Severity.HIGH
    minimum_confidence: float = Field(default=0.65, ge=0, le=1)
    require_human_for_breaking_api: bool = True


class GateDecision(StrictModel):
    status: GateStatus
    reasons: list[str]
    blocking_finding_ids: list[str] = Field(default_factory=list)
    review_finding_ids: list[str] = Field(default_factory=list)


class DecisionOption(StrictModel):
    id: Annotated[str, Field(pattern=r"^OPT-[A-Z0-9-]+$")]
    action: Literal["continue", "mitigate", "redirect", "pause", "stop", "buy"]
    initiative_id: str
    rationale: str
    estimated_cost_usd: int = Field(ge=0)
    estimated_annual_value_usd: int = Field(ge=0)
    launch_confidence: float = Field(ge=0, le=1)
    risk_reduction_percent: float = Field(ge=0, le=100)
    recommended: bool = False


class PortfolioMetric(StrictModel):
    name: str
    value: float
    unit: str
    description: str


class DecisionReport(StrictModel):
    report_id: str
    scenario_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executive_summary: str
    gate: GateDecision
    assessments: list[AgentAssessment]
    options: list[DecisionOption]
    metrics: list[PortfolioMetric]
    recommended_option_ids: list[str]
    human_accountability_note: str = (
        "Northstar supports judgment; accountable leaders own all consequential decisions."
    )
