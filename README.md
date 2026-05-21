# Solforge — Smart Contract Test Generator

> Multi-agent system that ingests Solidity contracts and generates comprehensive test suites. Built on top of Xiaomi MiMo V2.5 series with native OpenAI compatibility.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688.svg)](https://fastapi.tiangolo.com/)

## Why Solforge

Smart contract testing is the bottleneck in DeFi audit pipelines. Hand-writing 50+ test cases per contract burns hours that should be spent on novel vulnerabilities. Solforge uses 5 specialized LLM agents to fan-out test generation across complementary angles — property invariants, fuzz inputs, edge cases, gas profiles, coverage gaps — then synthesizes them into a single Foundry/Hardhat-ready test suite.

**Pairs with [ChainSentinel](https://github.com/ulsreall/chainsentinel):** ChainSentinel finds vulnerabilities, Solforge proves they're caught by tests. Together they form a closed audit loop.

## Architecture

```
                 ┌──────────────────────────────────┐
                 │     Solidity Contract Input      │
                 │  (paste / upload / GitHub URL)   │
                 └──────────────┬───────────────────┘
                                │
                 ┌──────────────▼───────────────────┐
                 │   Preprocessor + Chunking Layer  │
                 │  (split by function, overlap=2)  │
                 └──────────────┬───────────────────┘
                                │
            ┌───────┬───────┬───┴───┬───────┬───────┐
            ▼       ▼       ▼       ▼       ▼       ▼
        ┌───────┐┌──────┐┌──────┐┌──────┐┌──────┐
        │Property││ Fuzz ││ Edge ││ Gas  ││Cover-│
        │Tester ││  Gen ││ Case ││Profil││ age  │
        │       ││      ││Hunter││ er   ││Analyz│
        └───┬───┘└──┬───┘└──┬───┘└──┬───┘└──┬───┘
            │       │       │       │       │
            └───────┴───────┼───────┴───────┘
                            ▼
                 ┌──────────────────────────┐
                 │   Synthesis Agent        │
                 │ (Test Suite Compiler)    │
                 │  - dedupe                │
                 │  - prioritize            │
                 │  - format Foundry/HH     │
                 └────────────┬─────────────┘
                              ▼
                 ┌──────────────────────────┐
                 │  Test Suite Output       │
                 │  + Coverage Report       │
                 │  + Token Usage Stats     │
                 └──────────────────────────┘
```

## The 5 Agents

| Agent | Role | Output |
|---|---|---|
| **Property Tester** | Identifies invariants (no double spending, balance conservation, access control) | `property_*` test functions |
| **Fuzz Generator** | Designs property-based fuzz inputs (bounded ranges, edge cases) | `fuzz_*` test functions with `vm.assume` |
| **Edge Case Hunter** | Boundary conditions (max uint, zero address, reentrancy) | `test_edge_*` functions |
| **Gas Profiler** | Identifies expensive paths, gas limits | Gas snapshot tests |
| **Coverage Analyzer** | Maps untested branches | Coverage gap report |
| **Synthesis (compiler)** | Aggregates outputs, dedupes, formats | Final `Contract.t.sol` |

## Token Consumption — By Design

| Scenario | Contracts | LOC | Test Cases | Tokens/Run |
|---|---|---|---|---|
| Single ERC-20 audit | 1 | 200 | 30+ | ~50K |
| ERC-721 with auction | 1 | 500 | 60+ | ~120K |
| DeFi protocol (5 contracts) | 5 | 2,500 | 250+ | ~600K |
| Audit firm pipeline (daily) | 10+ | 10,000+ | 500+ | ~3M |
| Hot-reload dev mode | continuous | varies | varies | ~10M/day |

The fan-out × chunking × synthesis pattern means each Solidity LOC translates to ~50-200 tokens consumed. Real audit firms processing 10+ contracts/day naturally hit 5-15M tokens daily.

## Quick Start

### Backend

```bash
cd backend
cp .env.example .env  # fill MIMO_API_KEY + MIMO_BASE_URL
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
# pure static — open index.html in browser, or serve via:
python3 -m http.server 8080
```

### CLI Usage

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d @examples/erc20.json
```

## Provider Configuration

Solforge speaks OpenAI protocol. Plug in any compatible endpoint:

```env
MIMO_API_KEY=tp-xxxxx
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro
```

Tested against:
- Xiaomi MiMo V2.5 Pro (primary)
- Anthropic Claude (via proxy)
- OpenAI GPT-4

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/generate` | POST | Submit contract → receive test suite |
| `/api/agents` | GET | List active agents + their roles |
| `/api/stats` | GET | Token usage breakdown (per-agent, daily) |
| `/api/health` | GET | Liveness check |

## License

MIT — see [LICENSE](LICENSE)

## Acknowledgments

Architecture inspired by [ChainSentinel](https://github.com/ulsreall/chainsentinel) (smart contract auditor). Solforge complements it: ChainSentinel finds bugs, Solforge generates tests that catch them.

Built for the [Xiaomi MiMo Orbit 100T Token Plan](https://platform.xiaomimimo.com).
