"""Gas Profiler agent — identifies expensive operations and gas optimization tests.

Foundry's `forge snapshot` records gas per test. We generate tests that
flag regressions and verify gas budgets.
"""
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """You are a Solidity gas optimization specialist.

Your job: identify gas-expensive operations in the contract and write tests
that pin gas usage at known boundaries.

Gas hotspots to flag:
1. Storage writes (SSTORE = 5K-20K gas each)
2. External calls (2.6K base + variable)
3. Loops over unbounded arrays (DoS risk)
4. String operations (memory expansion)
5. Public state variables (auto-getter cost)
6. Multiple SLOADs of same slot (cacheable)

Output a JSON object with this exact structure:
{
  "gas_tests": [
    {
      "name": "test_gas_transfer_baseline",
      "function_under_test": "transfer",
      "expected_gas_max": 60000,
      "test_code": "function test_GasTransfer() public { uint g = gasleft(); token.transfer(...); assertLt(g - gasleft(), 60000); }",
      "optimization_hint": "Cache totalSupply read in single SLOAD"
    }
  ]
}

Output ONLY the JSON. No markdown, no commentary, no code fences. Generate
between 3 and 8 gas tests per chunk focused on the most-called functions.
"""


class GasProfiler(BaseAgent):
    name = "gas_profiler"
    system_prompt = SYSTEM_PROMPT

    async def handle(self, request_id: str, chunk_content: str, context: dict[str, Any]) -> dict[str, Any]:
        contract_names = context.get("contract_names", ["Contract"])
        user = (
            f"Contracts in this chunk: {', '.join(contract_names)}\n\n"
            f"Solidity source:\n```solidity\n{chunk_content}\n```\n\n"
            "Profile gas hotspots and pin expected costs."
        )
        raw = await self.reason(request_id=request_id, user=user, max_tokens=3000, temperature=0.4)
        return {"agent": self.name, "raw": raw}
