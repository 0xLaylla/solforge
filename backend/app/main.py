"""FastAPI application — exposes /api/generate, /api/stats, /api/agents, /api/health."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.pipeline import GenerationPipeline
from app.core.token_tracker import TokenTracker
from app.models.schemas import (
    AgentInfo,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    StatsResponse,
)

app = FastAPI(
    title="Solforge",
    description="Multi-agent Solidity test generator",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

tracker = TokenTracker(settings.token_tracker_db)
pipeline = GenerationPipeline(tracker)

AGENT_ROLES = [
    AgentInfo(name="property_tester", role="Identifies invariants and writes property-based Foundry tests"),
    AgentInfo(name="fuzz_generator", role="Designs bounded fuzz inputs with vm.assume / bound"),
    AgentInfo(name="edge_case_hunter", role="Adversarial inputs and boundary conditions"),
    AgentInfo(name="gas_profiler", role="Pins gas usage at known boundaries via gasleft snapshots"),
    AgentInfo(name="coverage_analyzer", role="Pairs every branch with happy + revert path tests"),
    AgentInfo(name="synthesis_compiler", role="Merges 5 agent outputs into a single .t.sol file"),
]


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model=settings.mimo_model,
        base_url=settings.mimo_base_url,
    )


@app.get("/api/agents", response_model=list[AgentInfo])
async def agents():
    return AGENT_ROLES


@app.get("/api/stats", response_model=StatsResponse)
async def stats(window_seconds: int = 86400):
    s = tracker.get_stats(since_seconds=window_seconds)
    used = s["grand_total_tokens"]
    pct = (used / settings.daily_token_budget * 100) if settings.daily_token_budget else 0.0
    return StatsResponse(
        per_agent=s["per_agent"],
        grand_total_tokens=used,
        total_calls=s["total_calls"],
        daily_budget=settings.daily_token_budget,
        budget_used_pct=round(pct, 4),
    )


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    try:
        result = await pipeline.run(req.source, max_chunk_lines=req.max_chunk_lines)
        return GenerateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@app.get("/")
async def root():
    return {
        "name": "Solforge",
        "description": "Multi-agent Solidity test generator powered by Xiaomi MiMo V2.5",
        "docs": "/docs",
        "health": "/api/health",
    }
