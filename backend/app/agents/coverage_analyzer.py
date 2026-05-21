"""Coverage Analyzer agent — maps untested branches and generates targeted tests.

Looks at branches (if/else/require/revert) and ensures both the happy path
and revert path have test cases.
"""
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """You are a Solidity test coverage specialist.

Your job: enumerate all conditional branches in the contract (if, require,
revert, modifier checks) and write tests that exercise BOTH paths.

For every branch, we want:
1. Test that triggers the truthy path (function succeeds)
2. Test that triggers the revert/falsy path (function fails as expected)

Pay attention to:
- Modifiers (onlyOwner, whenNotPaused, nonReentrant)
- require() statements with custom messages or errors
- if/else branches that change state differently
- Implicit branches (e.g., transfer returning false vs reverting)

Output a JSON object with this exact structure:
{
  "coverage_tests": [
    {
      "name": "test_onlyOwner_revertsForNonOwner",
      "branch": "modifier onlyOwner at line 42",
      "path": "revert",
      "test_code": "function test_RevertWhen_NonOwnerCalls() public { vm.prank(attacker); vm.expectRevert(); ... }"
    },
    {
      "name": "test_onlyOwner_succeedsForOwner",
      "branch": "modifier onlyOwner at line 42",
      "path": "happy",
      "test_code": "function test_OwnerCanCall() public { vm.prank(owner); ... }"
    }
  ],
  "uncovered_branches": [
    {
      "location": "function withdraw, line 78",
      "reason": "branch only reachable via specific oracle state — needs mock"
    }
  ]
}

Output ONLY the JSON. No markdown, no commentary, no code fences. Aim for
8 to 16 coverage tests per chunk; pair every branch with both happy and revert.
"""


class CoverageAnalyzer(BaseAgent):
    name = "coverage_analyzer"
    system_prompt = SYSTEM_PROMPT

    async def handle(self, request_id: str, chunk_content: str, context: dict[str, Any]) -> dict[str, Any]:
        contract_names = context.get("contract_names", ["Contract"])
        user = (
            f"Contracts in this chunk: {', '.join(contract_names)}\n\n"
            f"Solidity source:\n```solidity\n{chunk_content}\n```\n\n"
            "Enumerate branches and pair every one with happy + revert tests."
        )
        raw = await self.reason(request_id=request_id, user=user, max_tokens=4000, temperature=0.5)
        return {"agent": self.name, "raw": raw}
