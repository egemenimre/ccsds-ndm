# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O.

"""
from pathlib import Path

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
    issues and run debugging. """

    path_kvn = Path("data", "kvn", "504x0b1c1_fig3_8_apm.kvn")
    path_xml = Path("data", "kvn", "504x0b1c1_fig3_8_apm.xml")
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
    """Tests comparison of XML and KVN NDM files."""

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

        assert ndm_kvn_out_str == ndm_xml_out_str


def process_paths(working_dir, path):
    """
    Processes the path depending on the run environment.
    """
    file_path = working_dir.joinpath(path)
    if not working_dir.joinpath(file_path).exists():
        file_path = working_dir.joinpath(extra_path).joinpath(path)

    return file_path
