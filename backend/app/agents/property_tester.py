"""Property Tester agent — identifies invariants and writes property-based tests.

An invariant is a property that must hold true regardless of input.
For ERC-20: total supply == sum of balances. For Vault: assets ≥ shares × rate.
"""
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """You are a Solidity property-based test specialist.

Your job: read a smart contract chunk and identify invariants — properties that
MUST hold across any valid state transition. Then write Foundry-compatible
property tests.

Invariant categories to check:
1. Conservation: total supply unchanged unless mint/burn called
2. Access control: only authorized roles modify state
3. Monotonicity: counters increase, timestamps don't go backwards
4. Bounds: balances ≤ total supply, fees ≤ 100%
5. Reentrancy: no state change after external call

Output a JSON object with this exact structure:
{
  "invariants": [
    {
      "name": "invariant_total_supply_equals_sum_of_balances",
      "description": "Total supply must always equal sum of all individual balances",
      "test_code": "function invariant_totalSupply() public { ... }",
      "severity": "critical"
    }
  ]
}

Output ONLY the JSON. No markdown, no commentary, no code fences. Generate
between 3 and 8 invariants per chunk depending on complexity.
"""


class PropertyTester(BaseAgent):
    name = "property_tester"
    system_prompt = SYSTEM_PROMPT

    async def handle(self, request_id: str, chunk_content: str, context: dict[str, Any]) -> dict[str, Any]:
        contract_names = context.get("contract_names", ["Contract"])
        user = (
            f"Contracts in this chunk: {', '.join(contract_names)}\n\n"
            f"Solidity source:\n```solidity\n{chunk_content}\n```\n\n"
            "Identify invariants and emit property tests."
        )
        raw = await self.reason(request_id=request_id, user=user, max_tokens=3500, temperature=0.5)
        return {"agent": self.name, "raw": raw}
