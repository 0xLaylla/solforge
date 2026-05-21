# Example Run — ERC-20 SimpleToken

Real end-to-end run, recorded 2026-05-22.

## Input

A 60-line ERC-20 contract (`examples/erc20.json`):

```solidity
contract SimpleToken {
    function transfer(address, uint256) public returns (bool);
    function approve(address, uint256) public returns (bool);
    function transferFrom(address, address, uint256) public returns (bool);
    function mint(address, uint256) public onlyOwner;
}
```

## Pipeline Configuration

| Setting | Value |
|---|---|
| Provider | Xiaomi MiMo Token Plan |
| Model | `mimo-v2.5-pro` |
| Base URL | `https://token-plan-sgp.xiaomimimo.com/v1` |
| Chunks | 1 (60 lines fit in single chunk) |
| Agents | 5 specialized + 1 synthesis |

## Token Usage Breakdown

| Agent | Prompt | Completion | Total |
|---|---:|---:|---:|
| property_tester | 2,860 | 3,500 | 6,360 |
| fuzz_generator | 2,885 | 3,500 | 6,385 |
| edge_case_hunter | 2,881 | 3,500 | 6,381 |
| gas_profiler | 2,893 | 3,000 | 5,893 |
| coverage_analyzer | 2,998 | 1,566 | 4,564 |
| synthesis_compiler | 4,398 | 2,913 | 7,311 |
| **Total** | **18,915** | **17,979** | **36,894** |

## Performance

| Metric | Value |
|---|---|
| Wall clock | 275 seconds (~4.5 minutes) |
| Throughput | 134 tokens/second |
| Tests generated | 13 |
| Duplicate filtered by synthesis | 1 |

## Output Sample

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

    function test_approveToZeroAddress() public {
        token.approve(address(0), 100);
        assertEq(token.allowance(address(this), address(0)), 100);
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

Full output JSON (with raw agent outputs and metadata): [`example_run.json`](./example_run.json)

## Scaling Estimates

This run was a 60-line ERC-20 contract → 36,894 tokens. Scaling linearly:

| Contract | LOC | Estimated Tokens |
|---|---:|---:|
| Simple ERC-20 | 60 | ~37K (verified) |
| Standard ERC-721 | 200 | ~120K |
| ERC-721 with royalties + auction | 500 | ~300K |
| DeFi protocol (5 contracts) | 2,500 | ~1.5M |
| Audit firm daily pipeline | 10,000+ | ~6M+ |

Real-world audit firms processing 10+ contracts daily naturally hit 5-15M tokens per day. The chunking + multi-agent fan-out pattern is what makes this organic — not synthetic load.
