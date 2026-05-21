"""Edge Case Hunter agent — identifies boundary conditions and adversarial inputs.

Edge cases that real audit reports cite:
- max uint256, type(uint256).max
- zero address (transfer to 0x0)
- self-transfer (msg.sender == to)
- reentrancy via callback contracts
- block.timestamp manipulation by miners
- integer overflow/underflow (post-0.8.0 reverts; verify expected)
"""
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """You are a Solidity adversarial test specialist focused on
boundary conditions and edge cases that break naive implementations.

Categories to cover:
1. Numeric extremes: 0, 1, type(uint).max, type(uint).max - 1
2. Address extremes: zero address, contract self, address(this)
3. Time manipulation: now=0, now=type(uint).max, before deploy block
4. Reentrancy: callback during transfer/withdraw
5. Storage collision: proxy/implementation slot conflicts
6. Gas: out-of-gas during external call, gas griefing

Output a JSON object with this exact structure:
{
  "edge_cases": [
    {
      "name": "test_edge_transferToZeroAddress",
      "category": "address_extreme",
      "test_code": "function test_RevertWhen_transferToZero() public { ... }",
      "expected_behavior": "revert with ERC20InvalidReceiver",
      "real_world_exploit": "Lost tokens forever if not reverted"
    }
  ]
}

Output ONLY the JSON. No markdown, no commentary, no code fences. Generate
between 5 and 12 edge case tests per chunk.
"""


class EdgeCaseHunter(BaseAgent):
    name = "edge_case_hunter"
    system_prompt = SYSTEM_PROMPT

    async def handle(self, request_id: str, chunk_content: str, context: dict[str, Any]) -> dict[str, Any]:
        contract_names = context.get("contract_names", ["Contract"])
        user = (
            f"Contracts in this chunk: {', '.join(contract_names)}\n\n"
            f"Solidity source:\n```solidity\n{chunk_content}\n```\n\n"
            "Hunt edge cases and adversarial inputs."
        )
        raw = await self.reason(request_id=request_id, user=user, max_tokens=3500, temperature=0.7)
        return {"agent": self.name, "raw": raw}
