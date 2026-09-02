"""Risk-model constants. Version all material calculation assumptions."""

MODEL_VERSION = "1.0.0"
CRITICALITY_WEIGHTS = {
    "business_criticality": 0.30,
    "revenue_dependency": 0.25,
    "data_sensitivity": 0.20,
    "operational_dependency": 0.15,
    "internet_exposure": 0.10,
}
LIKELIHOOD_WEIGHTS = {
    "base_rate": 0.04,
    "cvss": 0.18,
    "exploitability": 0.16,
    "criticality": 0.16,
    "internet_exposure": 0.12,
    "vulnerability_age": 0.08,
    "threat_activity": 0.10,
    "incident_signal": 0.06,
}
CONTROL_REDUCTION_CAP = 0.80
LOSS_COMPONENTS = (
    "downtime_cost",
    "data_breach_cost",
    "recovery_cost",
    "regulatory_exposure",
    "legal_cost",
    "business_impact",
)
