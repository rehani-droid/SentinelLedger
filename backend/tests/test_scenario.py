from app.scenarios.service import simulate_privileged_mfa, simulate_scenario

def test_mfa_scenario_reduces_eal() -> None:
    result = simulate_privileged_mfa(before_eal=8_460_000, rollout_cost=1_200_000, current_privileged_coverage=.2, target_privileged_coverage=1)
    assert result["after_eal"] < result["before_eal"]

def test_generic_scenario_reports_assumptions_and_delay_impact() -> None:
    result = simulate_scenario(
        baseline_eal=1_000_000, mfa_enabled=True, current_privileged_coverage=.2,
        target_privileged_coverage=1, remediation_delay_days=30,
        selected_control="identity", investment_reduction=100_000,
        investment_cost=200_000, selected_investment="mfa",
    )
    assert result["scenario_eal"] < result["baseline_eal"]
    assert result["assumptions"]
    assert result["implementation_cost"] == 200_000
