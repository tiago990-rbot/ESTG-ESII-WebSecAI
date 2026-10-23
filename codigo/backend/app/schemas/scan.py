from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator
from app.core.targets import parse_target
from app.schemas.finding import FindingResponse


class ScanCreate(BaseModel):
    url: str = Field(min_length=3, max_length=500)
    authorized: bool = False

    @field_validator("url")
    @classmethod
    def valid_url(cls, value: str) -> str:
        return parse_target(value).url


class ScanCreated(BaseModel):
    message: str
    scan_id: int


class ScanListItem(BaseModel):
    id: int
    url: str
    domain: str
    created_at: datetime
    score: int
    risk_level: str
    summary: str
    findings_count: int = 0


class ScanDetail(BaseModel):
    id: int
    url: str
    domain: str
    created_at: datetime
    score: int
    risk_level: str
    summary: str
    details: dict[str, Any]
    findings: list[FindingResponse]
    findings_count: int = 0


class DomainCount(BaseModel):
    domain: str
    count: int


class ScanStats(BaseModel):
    total_scans: int
    average_score: float
    best_score: int | None
    worst_score: int | None
    last_scan_date: datetime | None
    top_domains: list[DomainCount]


class ScanComparison(BaseModel):
    current_scan_id: int
    previous_scan_id: int | None
    current_score: int
    previous_score: int | None
    score_delta: int | None
    current_findings_count: int
    previous_findings_count: int | None
    findings_delta: int | None
    message: str
