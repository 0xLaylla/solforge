# Solforge — Backend

FastAPI multi-agent service that generates Foundry test suites from Solidity source.

## Setup

```bash
# 1. Create virtualenv
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
# Edit .env: set MIMO_API_KEY (tp-xxxxx) and MIMO_BASE_URL

# 4. Run dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI).

## Smoke test

```bash
# Health check
curl http://localhost:8000/api/health

# List agents
curl http://localhost:8000/api/agents

# Generate from example
curl -X POST http://localhost:8000/api/generate \
     -H "Content-Type: application/json" \
     -d @../examples/erc20.json
```

## Endpoints

| Path | Method | Body | Returns |
|---|---|---|---|
| `/api/health` | GET | — | provider + model |
| `/api/agents` | GET | — | list of 6 agents and their roles |
| `/api/stats` | GET | `?window_seconds=86400` | per-agent token usage |
| `/api/generate` | POST | `{source, max_chunk_lines}` | full pipeline result |

## Project layout

```
backend/
├── app/
│   ├── agents/              # 5 specialized + 1 synthesis
│   │   ├── base.py          # shared LLM call + retry + tracking
│   │   ├── property_tester.py
│   │   ├── fuzz_generator.py
│   │   ├── edge_case_hunter.py
│   │   ├── gas_profiler.py
│   │   ├── coverage_analyzer.py
│   │   └── synthesis.py
│   ├── api/                 # (reserved for future routes)
│   ├── core/
│   │   ├── config.py        # pydantic-settings env loader
│   │   ├── preprocessor.py  # chunking + metadata extraction
│   │   ├── pipeline.py      # orchestrator
│   │   └── token_tracker.py # SQLite-backed usage counter
│   ├── models/
│   │   └── schemas.py       # request/response pydantic
│   └── main.py              # FastAPI app
├── .env.example
└── requirements.txt
```

## Notes

- All agents share `AsyncOpenAI` client configured against the MiMo Token Plan endpoint
- Pipeline runs 5 agents in parallel per chunk via `asyncio.gather`
- Failed agents return an error dict; synthesis still runs with partial outputs
- Tokens are recorded immediately after each call (before retry/timeout)
