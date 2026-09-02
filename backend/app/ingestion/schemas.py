from datetime import datetime
from pydantic import BaseModel, Field

class VulnerabilityEvent(BaseModel):
    source_id: str = Field(min_length=1, max_length=80)
    source_event_id: str = Field(min_length=1, max_length=100)
    asset_id: int = Field(gt=0)
    cve_id: str = Field(pattern=r"^CVE-\d{4}-\d{4,}$")
    cvss: float = Field(ge=0, le=10)
    exploitability: float = Field(ge=0, le=1)
    observed_at: datetime
