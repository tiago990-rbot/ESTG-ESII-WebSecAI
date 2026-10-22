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

class AnalystReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1, max_length=1400)
    observations: list[Claim] = Field(max_length=12)
    recommendations: list[Claim] = Field(max_length=8)
    limitations: list[str] = Field(min_length=1, max_length=10)

class Question(BaseModel):
    text: str = Field(min_length=5, max_length=500)


class RetryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Literal["technical", "urlhaus", "phishtank", "osint", "exposure", "kev", "ai"]
    authorized: bool = False
