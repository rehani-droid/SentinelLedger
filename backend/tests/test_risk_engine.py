from app.risk.engine import asset_criticality, cyber_var, eal, expected_loss, rosi

def test_eal_matches_frequency_times_loss() -> None:
    assert eal(0.1, 10_000_000) == 1_000_000

def test_financial_components_are_summed() -> None:
    assert expected_loss({"downtime_cost": 4, "recovery_cost": 6}) == 10

def test_criticality_is_bounded() -> None:
    assert .1 <= asset_criticality(business_criticality=1, revenue_dependency=1) <= 1

def test_var_percentiles_are_ordered() -> None:
    result = cyber_var(annual_probability=.5, expected_loss_per_incident=1_000_000, simulations=1000)
    assert result["median"] <= result["p90"] <= result["p95"] <= result["p99"]

def test_rosi() -> None:
    assert rosi(300, 100) == 200
