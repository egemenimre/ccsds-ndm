# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2021 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations for KVN.

"""
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytest

from ccsds_ndm.ndm_io import NDMFileFormats, NdmIo
from ccsds_ndm.ndm_kvn_io import NdmKvnIo

extra_path = Path("ccsds_ndm", "tests")

kvn_xml_file_paths = {
    "AEMv2_1": Path("data", "kvn", "adm-testcase04a_abbrev.kvn"),
    "AEMv2_2": Path("data", "kvn", "adm-testcase04a_multi.kvn"),
    "APMv2_1": Path("data", "kvn", "504x0b1c1_fig3_6_apm.kvn"),
    "APMv2_2": Path("data", "kvn", "504x0b1c1_fig3_8_apm.kvn"),
    "CDMv2": Path("data", "kvn", "cdm_example_section4.kvn"),
    "OEMv2_1": Path("data", "kvn", "odmv2-testcase6_abbrev.kvn"),
    "OEMv2_2": Path("data", "kvn", "odmv2-testcase7a_xxx.kvn"),
    "OMMv2_1": Path("data", "kvn", "omm1_st.kvn"),
    "OMMv2_2": Path("data", "kvn", "omm1_ct.kvn"),
    # This is OPM v2 but it is compatible with OPM v1
    "OPMv2_1": Path("data", "kvn", "502x0b2c1e2_fig3_2_opm.kvn"),
    # This is OPM v2 and is incompatible with v1
    "OPMv2_2": Path("data", "kvn", "502x0b2c1e2_fig3_4_opm.kvn"),
    "RDMv2": Path("data", "kvn", "508x1b1_figc_2_rdm.kvn"),
    "TDMv2": Path("data", "kvn", "tdm-testcase01b.kvn"),
    "NDMv2": None,
    "NDMv2_strip": None,
}


# def test_read_file():
#
#     path = Path("data", "kvn", "tdm_opt_data.kvn")
#
#     # *** read KVN files ***
#     working_dir = Path.cwd()
#
#     if path is not None:
#         kvn_path = process_paths(working_dir, path)
#
#         # read KVN file
#         ndm = NdmKvnIo().from_path(kvn_path)
#
#         # print(ndm)
#         print(NdmIo().to_string(ndm, NDMFileFormats.XML))


kvn_write_file_keys = [
    "AEMv2_1",
    "AEMv2_2",
    "APMv2_1",
    "APMv2_2",
    "CDMv2",
    "OEMv2_1",
    "OEMv2_2",
    "OMMv2_1",
    "OMMv2_2",
    "OPMv2_1",
    "OPMv2_2",
    "RDMv2",
    "TDMv2",
    # "NDMv2",
    # "NDMv2_strip",
]


@pytest.mark.parametrize("ndm_key", kvn_write_file_keys)
def test_write_data(ndm_key):
    path = kvn_xml_file_paths[ndm_key]

    working_dir = Path.cwd()

    if path is not None:
        kvn_path = process_paths(working_dir, path)

        # read KVN file
        ndm = NdmIo().from_path(kvn_path)

        # export file to KVN and compare
        kvn_string = NdmKvnIo().to_string(ndm)

        kvn_text = _text_to_list(kvn_string)
        kvn_text_truth = _text_to_list(kvn_path.read_text())

        # write to file
        # kvn_path.with_suffix(".txt").write_text(kvn_string)

        using_nominal_tests = True
        if using_nominal_tests:
            # compare strings - check whether each line matches (delete spaces)
            match_status = [
                " ".join(kvn_text[i]).replace(" ", "")
                == " ".join(text_truth).replace(" ", "")
                for i, text_truth in enumerate(kvn_text_truth)
            ]

            # Find the non-matching ones
            no_match_list = [i for i, match in enumerate(match_status) if not match]
            match_decimals_list = _check_detailed_match(
                no_match_list, kvn_text, kvn_text_truth
            )

            # either no_match_list should be empty or try_to_match_list should be
            # all True. This means that all initial mismatches are checked OK
            assert not no_match_list or all(match_decimals_list)

        else:
            # This enables us to see the differences easily, but will fail for string
            # differences (e.g "0.000"  is not equal to "0.0E-1")
            assert kvn_text == kvn_text_truth


@pytest.mark.parametrize("ndm_key, path", kvn_xml_file_paths.items())
def test_read_file_against_xml(ndm_key, path):
    # *** read KVN files ***
    working_dir = Path.cwd()

    if path is not None:
        kvn_path = process_paths(working_dir, path)

        # read KVN file
        ndm = NdmKvnIo().from_path(kvn_path)

        # read equivalent XML file
        ndm_truth = NdmIo().from_path(kvn_path.with_suffix(".xml"))

        # export both files to xml and compare
        xml_text = NdmIo().to_string(ndm, NDMFileFormats.XML)
        xml_text_truth = NdmIo().to_string(ndm_truth, NDMFileFormats.XML)

        # compare strings
        assert xml_text == xml_text_truth


def process_paths(working_dir, path):
    """
    Processes the path depending on the run environment.
    """
    file_path = working_dir.joinpath(path)
    if not working_dir.joinpath(file_path).exists():
        file_path = working_dir.joinpath(extra_path).joinpath(path)

    return file_path


def _check_detailed_match(no_match_list, kvn_text, kvn_text_truth):
    # Certain lines may be mismatched, one example is values reported
    # in scientific and decimal notation. Try to match them as float.
    # Split helps get rid of the units.
    match_decimals_list = []
    for i in no_match_list:
        data_line = kvn_text[i][0].split()
        truth_line = kvn_text_truth[i][0].split()
        # try matching each item as Decimal, if it fails then as str
        is_matching = False
        for j, item in enumerate(data_line):
            try:
                is_matching = Decimal(data_line[j]) == Decimal(truth_line[j])
            except InvalidOperation:
                is_matching = str(data_line[j]) == str(truth_line[j])
            if not is_matching:
                break

        match_decimals_list.append(is_matching)

    return match_decimals_list


def _text_to_list(text):
    """Converts text to list."""
    txt_list = [line.split("=") for line in text.split("\n") if line]
    txt_list = [[txt_inner.strip() for txt_inner in line] for line in txt_list]

    # clean up runaway empty lines
    return [line for line in txt_list if line[0].strip() != ""]
