def answer(question: str, enterprise_eal: float) -> dict[str, str | float]:
    normalized = question.casefold()
    if "highest financial" in normalized or "highest risk" in normalized:
        return {"intent": "highest_financial_risk", "answer": "Customer Payments DB is the current highest modelled financial-risk contributor.", "enterprise_eal": enterprise_eal}
    if "mfa" in normalized:
        return {"intent": "mfa_scenario", "answer": "Use the MFA scenario endpoint to calculate the verified before/after estimate.", "enterprise_eal": enterprise_eal}
    return {"intent": "unsupported", "answer": "I can answer approved risk, MFA scenario, and investment questions using structured backend data only.", "enterprise_eal": enterprise_eal}
