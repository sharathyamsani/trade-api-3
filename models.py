"""
Pydantic models for request / response validation.
"""
import time
from pydantic import BaseModel, Field


class AnalysisMetadata(BaseModel):
    generated_at: float = Field(default_factory=time.time)
    sources_used: list[str] = []
    analysis_model: str = "gemini"
    sector_normalized: str = ""


class AnalysisResponse(BaseModel):
    sector: str
    report: str = Field(..., description="Full markdown analysis report")
    metadata: AnalysisMetadata
    cached: bool = False


class SessionInfo(BaseModel):
    session_id: str
    created_at: float = Field(default_factory=time.time)
    last_active: float = Field(default_factory=time.time)
    request_count: int = 0
    sectors_analyzed: list[str] = []


class ErrorResponse(BaseModel):
    error: str
    status_code: int
    detail: str | None = None
