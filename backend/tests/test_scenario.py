from app.scenarios.service import simulate_privileged_mfa

def test_mfa_scenario_reduces_eal() -> None:
    result = simulate_privileged_mfa(before_eal=8_460_000, rollout_cost=1_200_000, current_privileged_coverage=.2, target_privileged_coverage=1)
    assert result["after_eal"] < result["before_eal"]
