"""Synthesis agent — aggregates outputs from all 5 specialized agents into a unified test suite.

Workflow:
1. Receive raw JSON outputs from PropertyTester, FuzzGenerator, EdgeCaseHunter, GasProfiler, CoverageAnalyzer
2. Dedupe overlapping tests (same name, same purpose)
3. Order by category and severity
4. Format as a single Foundry-compatible .t.sol file
"""
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """You are a Solidity test suite compiler.

You receive raw outputs from 5 specialized agents (property_tester,
fuzz_generator, edge_case_hunter, gas_profiler, coverage_analyzer). Your job
is to merge them into ONE Foundry-compatible test contract.

Rules:
1. Dedupe: if two agents propose tests with the same purpose, keep the higher
   severity / more specific one
2. Order: invariants first, fuzz tests, edge cases, coverage tests, gas tests last
3. Imports: Foundry standard (forge-std/Test.sol)
4. Setup: include a setUp() function that deploys the contract
5. Comments: brief comment above each test explaining its origin agent
6. Naming: ensure all test functions are unique
7. Output: a complete, valid Solidity 0.8.x test file

Output a JSON object with this exact structure:
{
  "test_file": "// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.20;\\n\\nimport ...",
  "summary": {
    "total_tests": 42,
    "by_category": {"invariant": 5, "fuzz": 8, "edge": 12, "coverage": 14, "gas": 3}
  },
  "skipped": [
    {"agent": "fuzz_generator", "name": "fuzz_X", "reason": "duplicate of property invariant_Y"}
  ]
}

Output ONLY the JSON. No markdown, no commentary, no code fences.
"""


class TestSuiteCompiler(BaseAgent):
    name = "synthesis_compiler"
    system_prompt = SYSTEM_PROMPT

    async def handle(self, request_id: str, chunk_content: str, context: dict[str, Any]) -> dict[str, Any]:
        # chunk_content is unused for synthesis; the real input is the agent_outputs dict in context
        agent_outputs = context.get("agent_outputs", {})
        contract_names = context.get("contract_names", ["Contract"])

        sections = []
        for agent_name, output in agent_outputs.items():
            sections.append(f"### Output from {agent_name}\n```json\n{output}\n```")

        user = (
            f"Target contract(s): {', '.join(contract_names)}\n\n"
            f"Combine the following 5 agent outputs into a unified Foundry test file.\n\n"
            + "\n\n".join(sections)
        )
        raw = await self.reason(request_id=request_id, user=user, max_tokens=8000, temperature=0.3)
        return {"agent": self.name, "raw": raw}
