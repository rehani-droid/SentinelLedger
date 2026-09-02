from app.optimization.portfolio import InvestmentOption, optimise

def test_optimizer_respects_budget_and_dependencies() -> None:
    prerequisite = InvestmentOption("a", "A", 40, 80)
    dependent = InvestmentOption("b", "B", 30, 100, depends_on=("a",))
    result = optimise([prerequisite, dependent], 70)
    assert {item.identifier for item in result["selected"]} == {"a", "b"}
    assert result["total_cost"] <= 70
