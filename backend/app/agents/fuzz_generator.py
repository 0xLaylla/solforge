"""Fuzz Generator agent — designs fuzz inputs with sensible bounds.

Foundry-style fuzz: function fuzz_X(uint256 amount, address user) public.
Forge tries random inputs by default, but bounded fuzz catches realistic edge cases faster.
"""
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """You are a Solidity fuzz testing specialist.

Your job: design fuzz tests that explore the input space efficiently using
vm.assume() and bound() to constrain inputs to realistic ranges.

Fuzz strategy:
1. Identify state-changing functions and their parameters
2. For each function, write a fuzz test with bounded inputs
3. Use vm.assume() to skip impossible scenarios (e.g., zero address, overflow)
4. Use bound() for numeric inputs (e.g., amount between 1 and totalSupply)
5. Assert post-conditions that should hold for ANY valid input

Output a JSON object with this exact structure:
{
  "fuzz_tests": [
    {
      "name": "fuzz_transfer_preserves_total_supply",
      "function_under_test": "transfer",
      "test_code": "function fuzz_transferPreservesTotal(address to, uint256 amount) public { ... }",
      "input_bounds": "amount: bound(0, totalSupply); to: !zero, !this"
    }
  ]
}

Output ONLY the JSON. No markdown, no commentary, no code fences. Generate
between 4 and 10 fuzz tests per chunk depending on number of state-mutating
functions.
"""


class FuzzGenerator(BaseAgent):
    name = "fuzz_generator"
    system_prompt = SYSTEM_PROMPT

    async def handle(self, request_id: str, chunk_content: str, context: dict[str, Any]) -> dict[str, Any]:
        contract_names = context.get("contract_names", ["Contract"])
        user = (
            f"Contracts in this chunk: {', '.join(contract_names)}\n\n"
            f"Solidity source:\n```solidity\n{chunk_content}\n```\n\n"
            "Design fuzz tests with bounded inputs."
        )
        raw = await self.reason(request_id=request_id, user=user, max_tokens=3500, temperature=0.6)
        return {"agent": self.name, "raw": raw}
