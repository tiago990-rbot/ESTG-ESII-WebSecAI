from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class InvestigationCreate(BaseModel):
    target: str = Field(default="", max_length=2000)
    kind: Literal["domain", "message"] = "domain"
    organization: str = Field(default="", max_length=150)
    product: str = Field(default="", max_length=80)
    message: str = Field(default="", max_length=8000)
    technical: bool = False
    authorized: bool = False
    optional_sources: list[Literal["phishtank", "exposure", "hibp_catalog", "urlscan"]] = Field(default_factory=list, max_length=4)
    demo: bool = False
    @model_validator(mode="after")
    def check_input(self):
        if self.demo:
            return self
        if self.technical and (not self.authorized or self.kind != "domain"):
            raise ValueError("A análise técnica exige um website próprio/autorizado.")
        if self.kind == "message" and len(self.message.strip()) < 10:
            raise ValueError("Introduza pelo menos 10 caracteres de mensagem.")
        if self.kind == "domain" and len(self.target.strip()) < 3:
            raise ValueError("Introduza o domínio ou URL.")
        return self

class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=900)
    evidence_ids: list[str] = Field(min_length=1, max_length=10)

class Judgement(Claim):
    kind: Literal["observation", "inference", "hypothesis"]
    confidence: Literal["low", "medium", "high"]
    caveat: str = Field(min_length=1, max_length=350)

class Correlation(Claim):
    evidence_ids: list[str] = Field(min_length=2, max_length=8)
    kind: Literal["contextual_link", "possible_link", "contradiction"]
    confidence: Literal["low", "medium", "high"]
    caveat: str = Field(min_length=1, max_length=350)

class IntelligenceAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Literal["history", "identity", "current_signals", "technical", "correlation", "priorities"]
    answer: str = Field(min_length=1, max_length=650)
    assessment: Literal["supported", "hypothesis", "insufficient"]
    confidence: Literal["low", "medium", "high"]
    evidence_ids: list[str] = Field(max_length=8)
    caveat: str = Field(min_length=1, max_length=300)

class PriorityAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priority: Literal["P1", "P2", "P3"]
    action: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=1, max_length=350)
    validation: str = Field(min_length=1, max_length=350)
    evidence_ids: list[str] = Field(min_length=1, max_length=8)

class IntelligenceAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conclusions: list[Judgement] = Field(max_length=4)
    correlations: list[Correlation] = Field(max_length=3)
    questions: list[IntelligenceAnswer] = Field(min_length=6, max_length=6)
    actions: list[PriorityAction] = Field(max_length=4)
    gaps: list[str] = Field(min_length=1, max_length=8)

class AnalystReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1, max_length=1400)
    observations: list[Claim] = Field(max_length=12)
    recommendations: list[Claim] = Field(max_length=8)
    limitations: list[str] = Field(min_length=1, max_length=10)
    # Old persisted summaries remain readable; new generations require this block.
    intelligence: IntelligenceAnalysis | None = None

class Question(BaseModel):
    text: str = Field(min_length=5, max_length=500)


class RetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["hibp_catalog", "urlscan", "technical", "urlhaus", "phishtank", "osint", "exposure", "kev", "ai"]
    authorized: bool = False


class EvidenceReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["unreviewed", "reviewed", "contested"]
    identity_status: Literal["unverified", "matches", "does_not_match", "uncertain"]
    note: str = Field(default="", max_length=2000)
    previous_review_id: int | None = Field(default=None, ge=1)
