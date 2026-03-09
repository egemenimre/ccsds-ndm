# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O.

"""

import dataclasses
from pathlib import Path
from typing import Any

import pytest

from ccsds_ndm.mapping import NDMFileFormats
from ccsds_ndm.ndm_io import NdmIo

extra_path = Path("ccsds_ndm", "tests")

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


def test_read_file():
    """This is just a read test for individual files to understand specific
    issues and run debugging."""

    path_kvn = Path("data", "kvn", "odmv2-testcase7a_xxx.kvn")
    path_xml = Path("data", "kvn", "odmv2-testcase7a_xxx.xml")
    # path = Path("data", "kvn", "adm-testcase04a_multi.kvn")

    # *** read KVN files ***
    working_dir = Path.cwd()

    if path_kvn is not None:
        kvn_path = process_paths(working_dir, path_kvn)
        xml_path = process_paths(working_dir, path_xml)

        # read KVN file
        ndm = NdmIo().from_path(kvn_path)

        # read KVN file
        ndm_xml = NdmIo().from_path(xml_path)

        # print(ndm)
        # print("-------------------------------------")
        # print(ndm_xml)

        print(NdmIo().to_string(ndm, NDMFileFormats.XML))
        print("-------------------------------------")
        print(NdmIo().to_string(ndm_xml, NDMFileFormats.XML))


@pytest.mark.parametrize("ndm_key, path", file_paths.items())
def test_compare_files(ndm_key, path: Path):
    """Tests comparison of XML and KVN NDM files.

    Reads the equivalent XML and KVN files and writes the contents to XML strings
    to be compared line by line."""

    working_dir = Path.cwd()

    # *** read XML files ***
    # *** should raise an error in case something goes wrong ***
    if path is not None:
        kvn_path = process_paths(working_dir, path.with_suffix(".kvn"))
        xml_path = process_paths(working_dir, path.with_suffix(".xml"))

        # Load XML and KVN files
        ndm_xml = NdmIo().from_path(xml_path)
        ndm_kvn = NdmIo().from_path(kvn_path)

        ndm_kvn_out_str = NdmIo().to_string(ndm_kvn, NDMFileFormats.XML)
        ndm_xml_out_str = NdmIo().to_string(ndm_xml, NDMFileFormats.XML)

        assert (
            ndm_kvn_out_str == ndm_xml_out_str
        ), f"[{ndm_key}] KVN and XML outputs differ"


@pytest.mark.parametrize("ndm_key, path", file_paths.items())
def test_compare_objects(ndm_key, path: Path):
    """Tests that XML and KVN files produce identical NDM xsdata objects.

    Recursively walks the full object tree and reports every field that
    differs, so the output gives a complete picture of which nested objects
    were initialised correctly and which were not.
    """

    working_dir = Path.cwd()

    if path is not None:
        kvn_path = process_paths(working_dir, path.with_suffix(".kvn"))
        xml_path = process_paths(working_dir, path.with_suffix(".xml"))

        ndm_xml = NdmIo().from_path(xml_path)
        ndm_kvn = NdmIo().from_path(kvn_path)

        diffs = _collect_diffs(ndm_kvn, ndm_xml, root=type(ndm_kvn).__name__)
        assert not diffs, (
            f"[{ndm_key}] {len(diffs)} field(s) differ between KVN and XML objects:\n"
            + "\n".join(
                f"  {path}: KVN={kvn!r}  XML={xml!r}" for path, kvn, xml in diffs
            )
        )


wrong_contents = [
    "THIS=is a wrong data \n More wrong data\n",
    "<THIS=is a wrong data \n More wrong data>\n",
]

not_implemented = {
    "OMMv2_1": Path("data", "json", "omm1_st.json"),
    "OMMv2_2": Path("data", "json", "omm1_ct.json"),
}


@pytest.mark.parametrize("source_data", wrong_contents)
def test_read_errs(source_data):
    with pytest.raises(ValueError):
        # this should throw an ValueError exception
        NdmIo().from_string(source_data)


@pytest.mark.parametrize("path", not_implemented.values())
def test_read_json_file(path):
    with pytest.raises(NotImplementedError):

        # *** read files ***
        # *** should raise an error in case something goes wrong ***
        if path is not None:
            json_path = process_paths(Path.cwd(), path)

            # this should throw an NotImplementedError exception
            NdmIo().from_path(json_path)


def test_write_json_string():
    """Tests writing JSON data as string."""
    with pytest.raises(NotImplementedError):
        # check path and correct if necessary
        ommv2_1 = Path("data", "kvn", "omm1_st.kvn")
        kvn_path = process_paths(Path.cwd(), ommv2_1)

        # read KVN file
        ndm = NdmIo().from_path(kvn_path)

        # read equivalent JSON file
        ndm_truth = NdmIo().from_path(kvn_path.with_suffix(".xml"))

        # export both files to JSON and compare
        kvn_text = NdmIo().to_string(ndm, NDMFileFormats.JSON)
        kvn_text_truth = NdmIo().to_string(ndm_truth, NDMFileFormats.JSON)

        # compare strings
        assert kvn_text_truth == kvn_text


def _collect_diffs(kvn_obj: Any, xml_obj: Any, root: str) -> list[tuple[str, Any, Any]]:
    """Recursively compare two NDM xsdata object trees.

    Returns a list of ``(dotted_path, kvn_value, xml_value)`` tuples for
    every leaf or subtree that differs between *kvn_obj* and *xml_obj*.
    """
    diffs: list[tuple[str, Any, Any]] = []

    # Different types are an immediate mismatch – no point descending further.
    if type(kvn_obj) is not type(xml_obj):
        diffs.append((root, kvn_obj, xml_obj))
        return diffs

    if dataclasses.is_dataclass(kvn_obj) and not isinstance(kvn_obj, type):
        for f in dataclasses.fields(kvn_obj):
            child_path = f"{root}.{f.name}"
            kvn_val = getattr(kvn_obj, f.name)
            xml_val = getattr(xml_obj, f.name)
            diffs.extend(_collect_diffs(kvn_val, xml_val, child_path))

    elif isinstance(kvn_obj, list):
        if len(kvn_obj) != len(xml_obj):
            diffs.append((f"{root}[len]", len(kvn_obj), len(xml_obj)))
        for i, (kv, xv) in enumerate(zip(kvn_obj, xml_obj)):
            diffs.extend(_collect_diffs(kv, xv, f"{root}[{i}]"))

    else:
        # Scalar leaf (str, int, float, Enum, None, …)
        if kvn_obj != xml_obj:
            diffs.append((root, kvn_obj, xml_obj))

    return diffs


def process_paths(working_dir, path):
    """
    Processes the path depending on the run environment.
    """
    file_path = working_dir.joinpath(path)
    if not working_dir.joinpath(file_path).exists():
        file_path = working_dir.joinpath(extra_path).joinpath(path)

    return file_path
