# Architecture

Solforge is a multi-agent system. Five specialized LLM agents fan out across a Solidity contract, then a synthesis agent compiles their outputs into one Foundry-ready test suite.

## Pipeline

```
Solidity source
   │
   ▼
Preprocessor + Chunker
   │  ── extract metadata (contracts, pragma, license, imports)
   │  ── split source into ~200-line chunks at function boundaries
   │  ── overlap=20 lines for context preservation
   ▼
Per-chunk fan-out (parallel)
   │
   ├── PropertyTester       → invariants
   ├── FuzzGenerator        → bounded fuzz tests
   ├── EdgeCaseHunter       → adversarial inputs
   ├── GasProfiler          → gas snapshots
   └── CoverageAnalyzer     → branch coverage
   │
   ▼
Cross-chunk merge
   │  ── group by agent across chunks
   │  ── preserve chunk attribution
   ▼
Synthesis Agent (TestSuiteCompiler)
   │  ── dedupe overlapping tests
   │  ── order: invariants > fuzz > edge > coverage > gas
   │  ── format as Foundry .t.sol
   ▼
Final output
   │  ── test_file (Solidity .t.sol string)
   │  ── summary (counts per category)
   │  ── token_usage (per-agent breakdown)
```

## Why fan-out

Each agent is a domain specialist with a focused system prompt. Running them in parallel exposes the contract to multiple complementary lenses simultaneously. The same chunk gets analyzed five different ways without artificial repetition.

## Why chunking

For contracts > 200 lines, processing the whole file at once forces the model to allocate attention thin across many functions. Chunking with overlap lets each chunk receive deep analysis while preserving cross-chunk context via the overlap window.

## Why synthesis

Raw agent outputs include duplicates (a property test may overlap with a coverage test) and conflicts (different naming for the same scenario). The synthesis agent reconciles these into one coherent file the developer can drop into `test/` and run with `forge test`.

## Token consumption pattern

For a 500-line contract chunked into 3 windows:

| Stage | Calls | Tokens (est.) |
|---|---|---|
| 5 agents × 3 chunks | 15 | ~75K |
| Synthesis | 1 | ~25K |
| Total per generation | 16 | ~100K |

Audit firms running 10+ generations per day naturally hit 1-3M tokens. Continuous monitoring during dev cycles (re-run on every contract change) hits 10M+ tokens daily.

## Failure modes & mitigations

| Failure | Mitigation |
|---|---|
| Agent timeout | Tenacity retry with exponential backoff (3 attempts) |
| Malformed JSON output | Synthesis agent receives raw text and is instructed to handle inconsistency |
| Token limit per call | Chunking caps input; max_tokens caps output |
| One agent failing | Pipeline catches exception per agent; synthesis runs with partial outputs |

## Storage

SQLite database (`./data/usage.db`) records per-call token usage. Stats endpoint queries this for real-time and historical breakdowns.

## Provider portability

All LLM calls go through `AsyncOpenAI` configured via `MIMO_BASE_URL` and `MIMO_API_KEY`. Swap to any OpenAI-compatible provider by changing `.env`:

```env
# Xiaomi MiMo Token Plan
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_API_KEY=tp-xxxxx
MIMO_MODEL=mimo-v2.5-pro

# OpenAI
MIMO_BASE_URL=https://api.openai.com/v1
MIMO_API_KEY=sk-xxxxx
MIMO_MODEL=gpt-4

# Anthropic via OpenAI-compat proxy
MIMO_BASE_URL=https://your-proxy/v1
MIMO_API_KEY=sk-ant-xxxxx
MIMO_MODEL=claude-3-5-sonnet
```
