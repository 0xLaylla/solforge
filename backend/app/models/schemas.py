"""Pydantic schemas for API request/response."""
from typing import Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    source: str = Field(..., min_length=20, description="Solidity source code")
    contract_name: Optional[str] = Field(None, description="Optional hint for primary contract")
    max_chunk_lines: int = Field(200, ge=50, le=1000)


class TokenUsageEntry(BaseModel):
    agent: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    timestamp: int


class GenerateResponse(BaseModel):
    request_id: str
    metadata: dict
    agent_outputs: dict
    synthesis: str
    token_usage: list[TokenUsageEntry]


class StatsResponse(BaseModel):
    per_agent: dict
    grand_total_tokens: int
    total_calls: int
    daily_budget: int
    budget_used_pct: float


class HealthResponse(BaseModel):
    status: str
    model: str
    base_url: str


class AgentInfo(BaseModel):
    name: str
    role: str
