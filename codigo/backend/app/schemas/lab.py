from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class SourceFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1,max_length=180)
    content: str = Field(max_length=30_000)

class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1,max_length=100)
    revision: str = Field(min_length=1,max_length=100)
    authorized: Literal[True]
    files: list[SourceFile] = Field(default_factory=list,max_length=40)
    zip_base64: str = Field(default="",max_length=1_400_000)

class ReportImport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: Literal["semgrep","osv","gitleaks"]
    version: str = Field(default="unknown",max_length=50)
    source_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    report_json: str = Field(max_length=1_000_000)

class CodeReviewRequest(BaseModel):
    # The user explicitly accepts sending selected, redacted code to the configured model.
    consent_external_ai: Literal[True]

class FindingReview(BaseModel):
    status: Literal["pending","confirmed","false_positive","fixed"]
    note: str = Field(min_length=5,max_length=1000)
    previous_sequence: int = Field(ge=0)

class CodeClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=3,max_length=150)
    severity: Literal["high","medium","low","info"]
    confidence: Literal["low","medium","high"]
    path: str = Field(max_length=180)
    line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    reasoning: str = Field(min_length=10,max_length=1600)
    recommendation: str = Field(min_length=5,max_length=1000)
    regression_test: str = Field(min_length=5,max_length=1000)
    related_paths: list[str] = Field(max_length=5)

class CodeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=10,max_length=2000)
    findings: list[CodeClaim] = Field(max_length=12)
    limitations: list[str] = Field(min_length=1,max_length=10)

class Correlation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_ids: list[str] = Field(min_length=2,max_length=6)
    explanation: str = Field(min_length=10,max_length=1000)
    validation: str = Field(min_length=10,max_length=1000)

class LabSynthesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=10,max_length=2000)
    priorities: list[str] = Field(max_length=12)
    correlations: list[Correlation] = Field(max_length=6)
    limitations: list[str] = Field(min_length=1,max_length=10)
