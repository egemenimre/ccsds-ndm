# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.

"""
Benchmark: measure each from_string() pipeline step for every KVN test file.

Steps timed independently:
  1. tokenize     - classify every input line
  2. parse_blocks - group tokens into a KvnDocument
  3. build_object - map KvnDocument onto the xsdata dataclass tree

Run with pytest:
  pytest -v ccsds_ndm/tests/test_benchmark.py
"""

import statistics
import timeit
from pathlib import Path

import pytest

from ccsds_ndm.kvn_utils_builder import build_object
from ccsds_ndm.kvn_utils_parser import parse_blocks
from ccsds_ndm.kvn_utils_tokenizer import tokenize

DATA_DIR = Path(__file__).parent / "data" / "kvn"
_benchmark_results = []


def _get_kvn_files():
    """Get KVN files, handling cases where directory doesn't exist."""
    files = sorted(DATA_DIR.glob("*.kvn"))
    if not files:
        pytest.skip(f"No KVN files found in {DATA_DIR}")
    return files


@pytest.fixture(params=_get_kvn_files())
def kvn_file(request):
    """Parametrized fixture that yields each KVN test file."""
    return request.param


@pytest.fixture(scope="session", autouse=True)
def print_summary():
    """Print benchmark summary table after all tests complete."""
    yield
    if not _benchmark_results:
        return
    col = 40
    print(
        f"\n{'File':<{col}} {'Lines':>6}  {'Mean':>10}  {'StdDev':>10}  "
        f"{'Tokenize (Mean)':>10}  {'ParseBlks (Mean)':>10}  {'BuildObj (Mean)':>10}"
    )
    print(
        f"{'-' * col} {'-' * 6}  {'-' * 10}  {'-' * 10}  {'-' * 10}  {'-' * 10}  {'-' * 10}"
    )
    for r in _benchmark_results:
        print(
            f"{r['file']:<{col}} {r['lines']:>6}  "
            f"{r['mean'] * 1000:>9.3f}ms  {r['stddev'] * 1000:>9.3f}ms  "
            f"{r['tokenize_mean'] * 1000:>9.3f}ms  {r['parse_blocks_mean'] * 1000:>9.3f}ms  "
            f"{r['build_object_mean'] * 1000:>9.3f}ms"
        )


class TestPipelinePerformance:
    """Benchmark tests for KVN parsing pipeline stages."""

    def test_full_pipeline(self, kvn_file):
        """Benchmark all three pipeline steps together."""
        src = kvn_file.read_text()

        def run_full_pipeline():
            lines = tokenize(src)
            doc = parse_blocks(lines)
            result = build_object(doc)
            return result

        # Verify test passes
        result = run_full_pipeline()
        assert result is not None

        # Run benchmark with 3 repeats, 10 iterations each
        times = timeit.repeat(run_full_pipeline, repeat=3, number=10)
        per_call = [t / 10 for t in times]

        # Benchmark individual steps
        def run_tokenize():
            return tokenize(src)

        def run_parse_blocks():
            lines = tokenize(src)
            return parse_blocks(lines)

        def run_build_object():
            lines = tokenize(src)
            doc = parse_blocks(lines)
            return build_object(doc)

        tokenize_times = timeit.repeat(run_tokenize, repeat=3, number=10)
        tokenize_per_call = [t / 10 for t in tokenize_times]

        parse_blocks_times = timeit.repeat(run_parse_blocks, repeat=3, number=10)
        parse_blocks_per_call = [t / 10 for t in parse_blocks_times]

        build_object_times = timeit.repeat(run_build_object, repeat=3, number=10)
        build_object_per_call = [t / 10 for t in build_object_times]

        _benchmark_results.append(
            {
                "file": kvn_file.name,
                "lines": len(src.splitlines()),
                "mean": sum(per_call) / len(per_call),
                "stddev": statistics.stdev(per_call),
                "min": min(per_call),
                "max": max(per_call),
                "tokenize_mean": sum(tokenize_per_call) / len(tokenize_per_call),
                "parse_blocks_mean": sum(parse_blocks_per_call)
                / len(parse_blocks_per_call),
                "build_object_mean": sum(build_object_per_call)
                / len(build_object_per_call),
            }
        )
