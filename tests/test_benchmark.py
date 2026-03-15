# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.

"""
Benchmark: measure each from_string() pipeline step for every KVN test file.

Steps timed independently:
  1. tokenize     - classify every input line
  2. parse_blocks - group tokens into a KvnDocument
  3. build_object - map KvnDocument onto the xsdata dataclass tree

Run with pytest:
  pytest -v tests/test_benchmark.py
"""

import statistics
import timeit
from pathlib import Path

import pytest

from ccsds_ndm.kvn_builder import build_object
from ccsds_ndm.kvn_parser import dispatch_document
from ccsds_ndm.kvn_tokenizer import tokenize

_LOCAL_DATA_DIR = Path(__file__).parent / "data" / "kvn"
_ROOT_DATA_DIR = Path.cwd() / "tests" / "data" / "kvn"
# When running from repo root (e.g. CI), __file__ is a relative path that may
# not resolve to the tests directory; fall back to cwd-relative path.
DATA_DIR = _LOCAL_DATA_DIR if _LOCAL_DATA_DIR.exists() else _ROOT_DATA_DIR
_benchmark_results: list = []


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
    c_file = 40
    c_lines = 6
    c_time = 12
    c_step = 18
    print(
        f"\n{'File':<{c_file}} {'Lines':>{c_lines}}  {'Mean':>{c_time}}  {'StdDev':>{c_time}}  "
        f"{'Tokenize (Mean)':>{c_step}}  {'ParseBlks (Mean)':>{c_step}}  {'BuildObj (Mean)':>{c_step}}"
    )
    print(
        f"{'-' * c_file} {'-' * c_lines}  {'-' * c_time}  {'-' * c_time}  {'-' * c_step}  {'-' * c_step}  {'-' * c_step}"
    )
    for r in _benchmark_results:
        print(
            f"{r['file']:<{c_file}} {r['lines']:>{c_lines}}  "
            f"{r['mean'] * 1000:>{c_time - 2}.3f}ms  {r['stddev'] * 1000:>{c_time - 2}.3f}ms  "
            f"{r['tokenize_mean'] * 1000:>{c_step - 2}.3f}ms  {r['parse_blocks_mean'] * 1000:>{c_step - 2}.3f}ms  "
            f"{r['build_object_mean'] * 1000:>{c_step - 2}.3f}ms"
        )


class TestPipelinePerformance:
    """Benchmark tests for KVN parsing pipeline stages."""

    def test_full_pipeline(self, kvn_file):
        """Benchmark all three pipeline steps together."""
        src = kvn_file.read_text()

        def run_full_pipeline():
            lines = tokenize(src)
            doc = dispatch_document(lines)
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
            return dispatch_document(lines)

        def run_build_object():
            lines = tokenize(src)
            doc = dispatch_document(lines)
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
