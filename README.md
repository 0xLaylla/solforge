# Solforge — Smart Contract Test Generator

> Multi-agent system that ingests Solidity contracts and generates comprehensive Foundry test suites. Built on top of Xiaomi MiMo V2.5 with native OpenAI compatibility.

## Why this exists

Smart contract auditors and DeFi developers spend 30-60% of their time writing tests. Most testing frameworks generate happy-path stubs and call it a day. Solforge fans out across **five complementary testing lenses** in parallel — property-based invariants, bounded fuzz, adversarial edge cases, gas profiling, and branch coverage — then synthesizes the outputs into one drop-in `.t.sol` file.

This is a token-hungry workload by design. A single ERC-20 contract triggers 6 LLM calls. A real DeFi protocol with 5 contracts × 500 lines triggers 30+ calls and consumes 1-2M tokens per generation. Audit firms running continuous test generation across their pipeline naturally hit 5-15M tokens per day.

## Real Run Numbers (Verified)

End-to-end execution recorded against two real contracts:

| Contract | LOC | Wall Clock | Tokens | Tests Generated |
|---|---:|---:|---:|---:|
| ERC-20 SimpleToken | 60 | 275s | **36,894** | 13 |
| Vault (deposit/withdraw + admin) | 137 | 282s | **44,643** | (synthesis full output) |

Both runs against `mimo-v2.5-pro` via the Token Plan endpoint. Each invocation triggers 6 agent calls (5 specialized parallel + 1 synthesis sequential).

Full breakdown: [`docs/EXAMPLE_RUN.md`](./docs/EXAMPLE_RUN.md) · raw outputs: [`docs/example_run.json`](./docs/example_run.json), [`docs/vault_run.json`](./docs/vault_run.json)

## Architecture — Six Specialized Agents

```
Solidity source
   │
   ▼
┌──────────────────────────────────────┐
│  Preprocessor + Chunker              │
│  - Extract metadata (contracts/pragma) │
│  - Split at function boundaries        │
│  - 200-line chunks with 20-line overlap│
└──────────────────────────────────────┘
   │
   ▼ (parallel fan-out)
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Property │   Fuzz   │   Edge   │   Gas    │ Coverage │
│  Tester  │Generator │  Case    │ Profiler │ Analyzer │
│          │          │  Hunter  │          │          │
│Invariants│ vm.assume│ adversa- │  pin gas │all branch│
│  + state │ + bound()│ rial bnd │  budgets │   pairs  │
│  preserv.│ inputs   │   cases  │          │  H+rev   │
└──────────┴──────────┴──────────┴──────────┴──────────┘
   │
   ▼ (sequential merge)
┌──────────────────────────────────────┐
│  Synthesis Compiler                  │
│  - Dedupe overlapping tests          │
│  - Order: invariants→fuzz→edge→cov→gas│
│  - Format as Foundry .t.sol          │
└──────────────────────────────────────┘
   │
   ▼
Foundry test file (drop into test/)
```

## Quick Start

### Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: MIMO_API_KEY=tp-xxxxx
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

### Frontend (vanilla JS — no build step)

```bash
cd frontend
python3 -m http.server 3000
# Open http://localhost:3000
```

Or deploy directly to Netlify (see `netlify.toml`).

### Smoke test the pipeline

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d @examples/erc20.json
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Provider + model status |
| `/api/agents` | GET | List of 6 agents and their roles |
| `/api/generate` | POST | Run full pipeline against Solidity source |
| `/api/stats` | GET | Per-agent token usage breakdown |

## Provider Compatibility

All LLM calls go through `AsyncOpenAI`. Swap providers via `.env`:

```env
# Xiaomi MiMo Token Plan (default)
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_API_KEY=tp-xxxxx
MIMO_MODEL=mimo-v2.5-pro

# OpenAI
MIMO_BASE_URL=https://api.openai.com/v1
MIMO_API_KEY=sk-xxxxx
MIMO_MODEL=gpt-4

# Any OpenAI-compatible proxy
```

## Token Consumption Profile

This workload is naturally token-hungry. Linear scaling estimates:

| Contract | LOC | Estimated Tokens |
|---|---:|---:|
| Simple ERC-20 | 60 | 37K (verified) |
| Standard ERC-721 | 200 | ~120K |
| ERC-721 + royalties + auction | 500 | ~300K |
| DeFi protocol (5 contracts) | 2,500 | ~1.5M |
| Audit firm daily pipeline | 10,000+ | ~6M+ |

The chunking + fan-out pattern is what makes this organic — not synthetic load. Every chunk gets analyzed five different ways simultaneously.

## Why Xiaomi MiMo V2.5

- **Native OpenAI compatibility** — drop-in via base URL
- **Reasoning content support** — visible chain-of-thought helps debug agent outputs
- **Cost-competitive at scale** — 700M tokens/month Pro tier is built for token-hungry workloads
- **Long context windows** — full contract chunks fit comfortably

## Repo Layout

```
solforge/
├── backend/
│   ├── app/
│   │   ├── agents/           # 5 specialized + synthesis
│   │   ├── core/             # config, pipeline, preprocessor, tracker
│   │   ├── models/           # pydantic schemas
│   │   └── main.py           # FastAPI entrypoint
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md             # backend setup details
├── frontend/
│   └── index.html            # vanilla JS dark-themed UI
├── docs/
│   ├── ARCHITECTURE.md       # design decisions
│   ├── EXAMPLE_RUN.md        # real run report
│   └── example_run.json      # raw output artifact
├── examples/
│   └── erc20.json            # sample input
├── netlify.toml              # frontend deploy config
└── LICENSE                   # MIT
```

## Roadmap

- [x] Multi-agent fan-out architecture
- [x] Token tracking with per-agent breakdown
- [x] Foundry-compatible synthesis
- [x] Dark-themed frontend
- [ ] Streaming responses (server-sent events)
- [ ] Brownie + Hardhat output formats
- [ ] Mutation testing integration
- [ ] CI mode (run on every push, fail on regression)

## License

MIT — see [LICENSE](./LICENSE).

---

Built for the [Xiaomi MiMo Open Source Incentive Program](https://platform.xiaomimimo.com/) · 2026
