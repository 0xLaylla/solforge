# Solforge — Verification Proofs

This folder contains evidence that Solforge is a real, functioning multi-agent system that consumes Xiaomi MiMo tokens at the rate claimed in the README and ARCHITECTURE docs.

## Files

| File | What it is |
|---|---|
| `terminal_screenshot.png` | Terminal capture of the pipeline running both example contracts end-to-end, with per-agent token counts visible. |
| `boot_log.txt` | Full structured log of two runs (ERC-20 SimpleToken + Vault) with per-agent invariants, fuzz strategies, edge cases, gas snapshots, coverage gaps, and synthesis output. Includes SQLite query verification and `/api/stats` JSON response. |
| `run_sample.txt` | Raw JSON output from the synthesis_compiler agent for the ERC-20 run — 13 Foundry-compatible test cases. |
| `../docs/EXAMPLE_RUN.md` | Markdown summary of both runs with token tables and scaling estimates. |
| `../docs/example_run.json` | Raw JSON output from the ERC-20 pipeline run. |
| `../docs/vault_run.json` | Raw JSON output from the Vault pipeline run. |

## How to verify

Anyone can reproduce these runs locally:

```bash
git clone https://github.com/0xLaylla/solforge
cd solforge/backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set MIMO_API_KEY=tp-xxxxx
uvicorn app.main:app --reload
```

Then in another shell:

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d @../examples/erc20.json
```

Token usage is recorded in `./data/usage.db` (SQLite). Query with:

```bash
sqlite3 ./data/usage.db "SELECT agent_name, SUM(total_tokens) FROM usage GROUP BY agent_name"
```

The exact numbers will vary slightly per run (model is non-deterministic), but the structure and order of magnitude will match.

## Summary numbers

| Metric | Run 1 (ERC-20, 60 LOC) | Run 2 (Vault, 137 LOC) |
|---|---:|---:|
| Wall clock | 275s | 282s |
| Total tokens | 36,894 | 44,643 |
| Tests generated | 13 | 17 |
| Throughput | 134 tok/s | 158 tok/s |
| Tokens per LOC | 615 | 326 |

Cumulative session: **81,537 tokens across 2 runs**.

## Production token economics

Interpolated from the verified runs (averaging 414 tokens/LOC after the synthesis dominance kicks in):

- Audit firm processing 10 contracts daily (1K LOC avg) → ~4M tokens/day
- DevOps team CI integration (every PR generates tests) → ~2-5M tokens/day
- Power user (1-2 contracts daily) → ~50-100K tokens/day

Token consumption is driven naturally by the multi-agent fan-out architecture, not artificially inflated.
