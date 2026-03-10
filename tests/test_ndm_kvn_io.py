# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations for KVN.

"""

from pathlib import Path

import pytest

from ccsds_ndm.mapping import NDMFileFormats
from ccsds_ndm.ndm_io import NdmIo
from tests.test_ndm_io import extra_path, process_paths

file_paths = {
    "OPM_1": Path("data", "kvn", "502x0b2c1e2_fig3_2_opm"),
    "OPM_2": Path("data", "kvn", "502x0b2c1e2_fig3_4_opm"),
    "OEM_1": Path("data", "kvn", "502x0b2c1e2_fig5_1_oem"),
    "OEM_2": Path("data", "kvn", "odmv2-testcase6_abbrev"),
    "OEM_3": Path("data", "kvn", "odmv2-testcase7a_xxx"),
    "APM_1": Path("data", "kvn", "504x0b1c1_fig3_6_apm"),
    "APM_2": Path("data", "kvn", "504x0b1c1_fig3_8_apm"),
    "RDM_1": Path("data", "kvn", "508x1b1_figc_2_rdm"),
    "ADM_1": Path("data", "kvn", "adm-testcase04a_abbrev"),
    "ADM_2": Path("data", "kvn", "adm-testcase04a_multi"),
    "CDM_1": Path("data", "kvn", "cdm_example_section4"),
    "OMM_1": Path("data", "kvn", "omm1_ct"),
    "OMM_2": Path("data", "kvn", "omm1_st"),
    "TDM_1": Path("data", "kvn", "tdm-testcase01b"),
}


# def test_read_file():

#     path = Path("data", "kvn", "504x0b1c1_fig3_8_apm.kvn")
#     # path = Path("data", "kvn", "adm-testcase04a_multi.kvn")

#     # *** read KVN files ***
#     working_dir = Path.cwd()

#     if path is not None:
#         kvn_path = process_paths(working_dir, path)

#         # read KVN file
#         ndm = NdmKvnIo().from_path(kvn_path)

# print(ndm)
# print(NdmKvnIo().to_string(ndm, NDMFileFormats.XML))


def test_write_multi_ndm_kvn():
    """Combi-NDM for KVN fail test."""
    with pytest.raises(NotImplementedError):
        # this should throw an NotImplementedError exception

        ndm_v2 = Path("data", "xml", "omm_combined.xml")

        # check path and correct if necessary
        kvn_path = Path.cwd().joinpath(ndm_v2)
        if not Path.cwd().joinpath(kvn_path).exists():
            kvn_path = Path.cwd().joinpath(extra_path).joinpath(ndm_v2)

        ndm = NdmIo().from_path(kvn_path)
        NdmIo().to_file(ndm, NDMFileFormats.KVN, Path("new.kvn"))


@pytest.mark.parametrize("ndm_key, path", file_paths.items())
def test_round_trip(ndm_key, path: Path):
    """Tests a full KVN round-trip.

    Reads the KVN file, exports to a KVN string, re-parses that string, exports
    it back to KVN again, and compares the two KVN strings."""

    working_dir = Path.cwd()

    if path is not None:
        kvn_path = process_paths(working_dir, path.with_suffix(".kvn"))

        ndm = NdmIo().from_path(kvn_path)
        kvn_str_1 = NdmIo().to_string(ndm, NDMFileFormats.KVN)

        ndm_reread = NdmIo().from_string(kvn_str_1)
        kvn_str_2 = NdmIo().to_string(ndm_reread, NDMFileFormats.KVN)

        assert (
            kvn_str_1 == kvn_str_2
        ), f"[{ndm_key}] KVN round-trip produced different output"


@pytest.mark.parametrize("ndm_key, path", file_paths.items())
def test_write_files(ndm_key, path: Path):
    """Tests that the KVN writer produces the same keywords as the original file.

    Reads the KVN file, builds the object, writes it back to a KVN string,
    and compares the ordered list of keyword names. Values are intentionally
    excluded because float formatting may differ (e.g. '.83483E-4' vs
    '8.3483e-05') while remaining semantically identical."""

    working_dir = Path.cwd()

    if path is not None:
        kvn_path = process_paths(working_dir, path.with_suffix(".kvn"))

        ndm = NdmIo().from_path(kvn_path)
        kvn_out = NdmIo().to_string(ndm, NDMFileFormats.KVN)

        original = kvn_path.read_text()

        def extract_kv_keys(text):
            """Return sorted list of keyword names from KV lines (those containing '=').

            Packed data lines and section markers are ignored — their content
            is covered by test_compare_objects."""
            return sorted(
                stripped.split("=")[0].strip()
                for line in text.splitlines()
                if (stripped := line.strip())
                and "=" in stripped
                and not stripped.startswith("COMMENT")
            )

        assert extract_kv_keys(kvn_out) == extract_kv_keys(
            original
        ), f"[{ndm_key}] KVN writer produced different keywords than the original file"
