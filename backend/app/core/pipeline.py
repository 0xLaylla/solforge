"""Pipeline orchestrator — runs all agents in parallel, then synthesis.

Flow:
1. Preprocess source → extract metadata + chunks
2. Per chunk: fan out to 5 specialized agents (parallel)
3. Aggregate per-chunk outputs
4. Synthesis agent compiles unified test suite
5. Return final test file + token usage breakdown
"""
import asyncio
import uuid

from app.agents.coverage_analyzer import CoverageAnalyzer
from app.agents.edge_case_hunter import EdgeCaseHunter
from app.agents.fuzz_generator import FuzzGenerator
from app.agents.gas_profiler import GasProfiler
from app.agents.property_tester import PropertyTester
from app.agents.synthesis import TestSuiteCompiler
from app.core.preprocessor import chunk_contract, extract_metadata
from app.core.token_tracker import TokenTracker


class GenerationPipeline:
    def __init__(self, tracker: TokenTracker):
        self.tracker = tracker
        self.specialized = [
            PropertyTester(tracker),
            FuzzGenerator(tracker),
            EdgeCaseHunter(tracker),
            GasProfiler(tracker),
            CoverageAnalyzer(tracker),
        ]
        self.synth = TestSuiteCompiler(tracker)

    async def run(self, source: str, max_chunk_lines: int = 200) -> dict:
        request_id = uuid.uuid4().hex
        meta = extract_metadata(source)
        chunks = chunk_contract(source, max_chunk_lines=max_chunk_lines)

        context = {
            "contract_names": meta.contract_names,
            "pragma": meta.pragma,
            "license": meta.license,
        }

        # Per-chunk fan-out across 5 agents
        per_chunk_outputs = []
        for chunk in chunks:
            agent_tasks = [
                agent.handle(request_id, chunk.content, context) for agent in self.specialized
            ]
            results = await asyncio.gather(*agent_tasks, return_exceptions=True)
            chunk_dict = {}
            for agent, res in zip(self.specialized, results):
                if isinstance(res, Exception):
                    chunk_dict[agent.name] = {"error": str(res)}
                else:
                    chunk_dict[agent.name] = res.get("raw", "")
            per_chunk_outputs.append({"chunk": chunk.name, "outputs": chunk_dict})

        # Merge same-agent outputs across chunks
        merged: dict[str, list] = {a.name: [] for a in self.specialized}
        for entry in per_chunk_outputs:
            for agent_name, raw in entry["outputs"].items():
                merged[agent_name].append({"chunk": entry["chunk"], "raw": raw})

        # Synthesis
        synth_context = {
            "contract_names": meta.contract_names,
            "agent_outputs": merged,
        }
        synth_result = await self.synth.handle(request_id, "", synth_context)

        return {
            "request_id": request_id,
            "metadata": {
                "contracts": meta.contract_names,
                "pragma": meta.pragma,
                "license": meta.license,
                "total_lines": meta.total_lines,
                "function_count": meta.function_count,
                "chunk_count": len(chunks),
            },
            "agent_outputs": merged,
            "synthesis": synth_result.get("raw", ""),
            "token_usage": self.tracker.get_request_breakdown(request_id),
        }
