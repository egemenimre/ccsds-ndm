# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2021 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations for KVN.

"""
from pathlib import Path

import pytest

from ccsds_ndm.ndm_io import NDMFileFormats, NdmIo
from ccsds_ndm.ndm_kvn_io import NdmKvnIo

extra_path = Path("ccsds_ndm", "tests")

kvn_xml_file_paths = {
    "AEMv1": None,
    "APMv1_1": Path("data", "kvn", "504x0b1c1_fig3_6_apm.kvn"),
    "APMv1_2": Path("data", "kvn", "504x0b1c1_fig3_8_apm.kvn"),
    "CDMv1": Path("data", "kvn", "cdm_example_section4.kvn"),
    "OEMv2_1": Path("data", "kvn", "odmv2-testcase6_abbrev.kvn"),
    "OEMv2_2": Path("data", "kvn", "odmv2-testcase7a_xxx.kvn"),
    "OMMv1_1": Path("data", "kvn", "omm1_st.kvn"),
    "OMMv1_2": Path("data", "kvn", "omm1_ct.kvn"),
    # This is OPM v2 but it is compatible with OPM v1
    "OPMv1_1": Path("data", "kvn", "502x0b2c1e2_fig3_2_opm.kvn"),
    # This is OPM v2 and is incompatible with v1
    # "OPMv2_1": Path("data", "kvn", "502x0b2c1e2_fig3_4_opm.kvn"),
    "RDMv1": Path("data", "kvn", "508x1b1_figc_2_rdm.kvn"),
    "TDMv1": None,
    "NDMv1": None,
    "NDMv1_strip": None,
}

# kvn_file_paths = {
#     # "AEMv1": Path("data", "kvn", "adm-testcase04a.kvn"),
#     # "APMv1_2": Path("data", "kvn", "504x0b1c1_fig3_8_apm.kvn"),
#     # "CDMv1": Path("data", "kvn", "cdm_example_section4.kvn"),
#     "OEMv2_1": Path("data", "kvn", "odmv2-testcase7a.kvn"),
#     # "OMMv1_1": Path("data", "kvn", "omm1_st.kvn"),
#     # "OMMv1_2": Path("data", "kvn", "omm1_ct.kvn"),
#     # "OPMv1_1": Path("data", "kvn", "502x0b2c1e2_fig3_2_opm.kvn"),
#     # "OPMv2_1": Path("data", "kvn", "502x0b2c1e2_fig3_4_opm.kvn"),
#     # "RDMv1": Path("data", "kvn", "508x1b1_figc_2_rdm.kvn"),
#     # "TDMv1": None,
#     # "NDMv1": None,
#     # "NDMv1_strip": None,
# }
#
#
# @pytest.mark.parametrize("ndm_key, path", kvn_file_paths.items())
# def test_read_file(ndm_key, path):
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
#         # print(NdmXmlIo().to_string(ndm))


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
