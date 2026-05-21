"""Solidity contract preprocessor — chunking & metadata extraction.

Splits a contract file into manageable chunks for parallel agent processing.
Strategy: split by function declarations with overlap to preserve context.
"""
import re
from dataclasses import dataclass


@dataclass
class ContractChunk:
    name: str
    content: str
    function_count: int
    line_start: int
    line_end: int


@dataclass
class ContractMetadata:
    contract_names: list[str]
    pragma: str
    license: str
    imports: list[str]
    total_lines: int
    function_count: int


FUNCTION_PATTERN = re.compile(
    r"function\s+(\w+)\s*\([^)]*\)\s*(?:public|external|internal|private)?\s*(?:view|pure|payable)?\s*(?:returns\s*\([^)]*\))?\s*\{",
    re.MULTILINE,
)
CONTRACT_PATTERN = re.compile(r"contract\s+(\w+)", re.MULTILINE)
PRAGMA_PATTERN = re.compile(r"pragma\s+solidity\s+([^;]+);")
LICENSE_PATTERN = re.compile(r"//\s*SPDX-License-Identifier:\s*([^\n]+)")
IMPORT_PATTERN = re.compile(r'import\s+["\']([^"\']+)["\']', re.MULTILINE)


def extract_metadata(source: str) -> ContractMetadata:
    return ContractMetadata(
        contract_names=CONTRACT_PATTERN.findall(source),
        pragma=(PRAGMA_PATTERN.search(source).group(1).strip() if PRAGMA_PATTERN.search(source) else "unknown"),
        license=(LICENSE_PATTERN.search(source).group(1).strip() if LICENSE_PATTERN.search(source) else "UNLICENSED"),
        imports=IMPORT_PATTERN.findall(source),
        total_lines=source.count("\n") + 1,
        function_count=len(FUNCTION_PATTERN.findall(source)),
    )


def chunk_contract(source: str, max_chunk_lines: int = 200, overlap_lines: int = 20) -> list[ContractChunk]:
    """Split contract into overlapping chunks for parallel processing.

    Small contracts (< max_chunk_lines) return as single chunk.
    Large contracts split at function boundaries with overlap.
    """
    lines = source.split("\n")
    if len(lines) <= max_chunk_lines:
        return [
            ContractChunk(
                name="full",
                content=source,
                function_count=len(FUNCTION_PATTERN.findall(source)),
                line_start=1,
                line_end=len(lines),
            )
        ]

    chunks = []
    # Find function boundaries
    function_starts = [m.start() for m in FUNCTION_PATTERN.finditer(source)]
    if not function_starts:
        # Fallback: arbitrary line splits
        for i in range(0, len(lines), max_chunk_lines - overlap_lines):
            chunk_lines = lines[i : i + max_chunk_lines]
            chunks.append(
                ContractChunk(
                    name=f"chunk_{i}",
                    content="\n".join(chunk_lines),
                    function_count=0,
                    line_start=i + 1,
                    line_end=min(i + max_chunk_lines, len(lines)),
                )
            )
        return chunks

    # Find line numbers for function starts
    line_offsets = []
    cum = 0
    for line in lines:
        line_offsets.append(cum)
        cum += len(line) + 1

    function_lines = []
    for start in function_starts:
        for i, off in enumerate(line_offsets):
            if off > start:
                function_lines.append(i)
                break
        else:
            function_lines.append(len(lines))

    # Group functions into chunks
    chunk_idx = 0
    cur_start = 0
    while cur_start < len(lines):
        cur_end = min(cur_start + max_chunk_lines, len(lines))
        # Snap end to nearest function boundary
        for fl in function_lines:
            if cur_start < fl <= cur_end:
                cur_end = fl
        chunk_text = "\n".join(lines[max(0, cur_start - overlap_lines) : cur_end])
        funcs_in_chunk = sum(1 for fl in function_lines if cur_start <= fl < cur_end)
        chunks.append(
            ContractChunk(
                name=f"chunk_{chunk_idx}",
                content=chunk_text,
                function_count=funcs_in_chunk,
                line_start=max(1, cur_start - overlap_lines + 1),
                line_end=cur_end,
            )
        )
        chunk_idx += 1
        cur_start = cur_end

    return chunks
