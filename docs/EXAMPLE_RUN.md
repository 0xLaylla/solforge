# Example Runs — Real Verification Data

Two real end-to-end runs recorded against `mimo-v2.5-pro` via Xiaomi MiMo Token Plan endpoint. All token counts come from the OpenAI usage object returned by the API.

## Run 1 — ERC-20 SimpleToken (60 lines)

A canonical ERC-20 contract: transfer, approve, transferFrom, mint with onlyOwner.

### Pipeline Configuration

| Setting | Value |
|---|---|
| Provider | Xiaomi MiMo Token Plan |
| Model | `mimo-v2.5-pro` |
| Base URL | `https://token-plan-sgp.xiaomimimo.com/v1` |
| Chunks | 1 (60 lines fit in single chunk) |
| Agents | 5 specialized + 1 synthesis |

### Token Usage Breakdown

| Agent | Prompt | Completion | Total |
|---|---:|---:|---:|
| property_tester | 2,860 | 3,500 | 6,360 |
| fuzz_generator | 2,885 | 3,500 | 6,385 |
| edge_case_hunter | 2,881 | 3,500 | 6,381 |
| gas_profiler | 2,893 | 3,000 | 5,893 |
| coverage_analyzer | 2,998 | 1,566 | 4,564 |
| synthesis_compiler | 4,398 | 2,913 | 7,311 |
| **Total** | **18,915** | **17,979** | **36,894** |

### Performance

| Metric | Value |
|---|---|
| Wall clock | 275 seconds |
| Throughput | 134 tokens/sec |
| Tests generated | 13 |
| Duplicates filtered by synthesis | 1 |

## Run 2 — Vault Contract (137 lines)

A real-world deposit/withdraw vault with shares, fees, lock period, whitelist, and admin controls.

### Token Usage Breakdown

| Agent | Prompt | Completion | Total |
|---|---:|---:|---:|
| property_tester | 3,548 | 3,500 | 7,048 |
| fuzz_generator | 3,573 | 3,500 | 7,073 |
| edge_case_hunter | 3,569 | 3,500 | 7,069 |
| gas_profiler | 3,581 | 3,000 | 6,581 |
| coverage_analyzer | 3,686 | 2,729 | 6,415 |
| synthesis_compiler | 6,008 | 4,449 | 10,457 |
| **Total** | **23,965** | **20,678** | **44,643** |

### Performance

| Metric | Value |
|---|---|
| Wall clock | 282 seconds |
| Throughput | 158 tokens/sec |

## Output Sample (Run 1)

The synthesis agent merged outputs from all 5 specialized agents into a single Foundry-compatible test file. Excerpt:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/SimpleToken.sol";

contract SimpleTokenTest is Test {
    SimpleToken token;
    address owner;
    uint256 constant INITIAL_SUPPLY = 1_000e18;

    function setUp() public {
        owner = address(this);
        token = new SimpleToken(INITIAL_SUPPLY);
    }

    // === EDGE CASE TESTS (edge_case_hunter) ===
    function test_transferZeroAmount() public {
        bool result = token.transfer(address(1), 0);
        assertTrue(result);
    }

    // === COVERAGE TESTS (coverage_analyzer) ===
    function test_OwnerCanMint() public {
        vm.prank(owner);
        token.mint(address(0xBEEF), 100e18);
        assertEq(token.balanceOf(address(0xBEEF)), 100e18);
    }

    function test_RevertWhen_NonOwnerCallsMint() public {
        vm.prank(address(0xDEAD));
        vm.expectRevert("not owner");
        token.mint(address(0xDEAD), 100e18);
    }

    // ... 9 more coverage tests, 1 dedupe via synthesis
}
```

Full output JSON (with raw agent outputs): [`example_run.json`](./example_run.json), [`vault_run.json`](./vault_run.json)

## Scaling Estimates

Two verified runs let us interpolate token consumption per LOC:

| Run | LOC | Tokens | Tokens/LOC |
|---|---:|---:|---:|
| ERC-20 | 60 | 36,894 | 615 |
| Vault | 137 | 44,643 | 326 |
| Average | — | — | ~450 |

The Vault run shows non-linear scaling: more LOC means richer context per agent, but synthesis dominates output cost.

| Contract Profile | Estimated LOC | Estimated Tokens |
|---|---:|---:|
| Standard ERC-721 | 200 | ~80K |
| ERC-721 + royalties + auction | 500 | ~180K |
| DeFi lending pool | 1,000 | ~350K |
| Full DeFi protocol (5 contracts) | 2,500 | ~1.0M |
| Audit firm daily pipeline | 10,000+ | ~4M+ |

Real-world audit firms processing 10+ contracts daily naturally hit 4-8M tokens per day. The chunking + multi-agent fan-out pattern is what makes this organic — not synthetic load. Every chunk gets analyzed five different ways simultaneously.
