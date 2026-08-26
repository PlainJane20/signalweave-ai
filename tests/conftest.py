from __future__ import annotations

import pytest

from northstar.contracts import (
    ApiChange,
    Initiative,
    Objective,
    ProgramScenario,
    Service,
    Team,
)


@pytest.fixture
def baseline_scenario() -> ProgramScenario:
    """A valid scenario containing intentional cross-domain risk signals."""
    return ProgramScenario(
        id="SCN-MARKETPLACE",
        title="Synthetic marketplace launch",
        organization="Northwind Marketplace (synthetic)",
        objectives=[
            Objective(
                id="OBJ-GROWTH",
                name="Increase trusted marketplace adoption",
                weight=0.65,
                target_metric="Increase activated customers by 20 percent",
            ),
            Objective(
                id="OBJ-RELIABILITY",
                name="Protect platform reliability",
                weight=0.35,
                target_metric="Maintain 99.95 percent availability",
            ),
        ],
        teams=[
            Team(
                id="TEAM-PLATFORM",
                name="Platform",
                available_engineers=4,
                quarterly_capacity_points=100,
            ),
            Team(
                id="TEAM-MOBILE",
                name="Mobile",
                available_engineers=5,
                quarterly_capacity_points=120,
            ),
        ],
        initiatives=[
            Initiative(
                id="INIT-IDENTITY",
                name="Identity API v2",
                owner_team_id="TEAM-PLATFORM",
                objective_ids=["OBJ-GROWTH", "OBJ-RELIABILITY"],
                required_capacity_points=125,
                required_engineers=5,
                annual_cost_usd=600_000,
                expected_annual_value_usd=1_900_000,
                strategic_value=92,
                delivery_confidence=0.58,
                target_quarter=3,
                alternative_vendor_cost_usd=740_000,
                systems=["SVC-IDENTITY"],
            ),
            Initiative(
                id="INIT-MOBILE",
                name="Mobile subscription launch",
                owner_team_id="TEAM-MOBILE",
                objective_ids=["OBJ-GROWTH"],
                dependency_ids=["INIT-IDENTITY"],
                required_capacity_points=95,
                required_engineers=4,
                annual_cost_usd=800_000,
                expected_annual_value_usd=2_500_000,
                strategic_value=88,
                delivery_confidence=0.72,
                target_quarter=2,
                systems=["SVC-IDENTITY"],
            ),
            Initiative(
                id="INIT-ORPHAN",
                name="Experimental engagement widget",
                owner_team_id=None,
                objective_ids=[],
                required_capacity_points=30,
                required_engineers=2,
                annual_cost_usd=250_000,
                expected_annual_value_usd=80_000,
                strategic_value=18,
                delivery_confidence=0.4,
                target_quarter=2,
            ),
        ],
        services=[
            Service(
                id="SVC-IDENTITY",
                name="Identity service",
                replicas=1,
                recovery_time_minutes=180,
                contains_phi=False,
                encryption_at_rest=True,
                audit_logging=True,
            )
        ],
        api_changes=[
            ApiChange(
                id="API-IDENTITY-V2",
                service_id="SVC-IDENTITY",
                consumer_team_ids=["TEAM-MOBILE"],
                backward_compatible=False,
                compatibility_window_days=0,
            )
        ],
        constraints=["Platform capacity cannot exceed quarterly allocation"],
    )
