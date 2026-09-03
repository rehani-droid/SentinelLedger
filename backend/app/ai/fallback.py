"""Small compatibility helper for the offline decision-support mode."""

def answer(question: str, enterprise_eal: float) -> dict[str, str | float]:
    normalized = question.casefold()
    if "mfa" in normalized:
        intent = "scenario_simulation"
    elif any(term in normalized for term in ("invest", "budget", "spend", "risk reduction")):
        intent = "investment_recommendation"
    elif any(term in normalized for term in ("asset", "financial", "exposure")):
        intent = "asset_risk"
    elif any(term in normalized for term in ("risk", "vulnerab", "cyber")):
        intent = "risk_overview"
    else:
        intent = "unsupported"
    return {"intent": intent, "enterprise_eal": enterprise_eal}
