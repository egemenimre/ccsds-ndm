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

kvn_file_paths = {
    "AEMv1": None,
    "APMv1": None,
    "CDMv1": Path("data", "kvn", "cdm_example_section4.kvn"),
    "OEMv1": None,
    "OMMv1_1": Path("data", "kvn", "omm1_st.kvn"),
    "OMMv1_2": Path("data", "kvn", "omm1_ct.kvn"),
    "OPMv1": None,
    "RDMv1": None,
    "TDMv1": None,
    "NDMv1": None,
    "NDMv1_strip": None,
}


@pytest.mark.parametrize("ndm_key, path", kvn_file_paths.items())
def test_read_file(ndm_key, path):
    # *** read KVN files ***
    working_dir = Path.cwd()

    if path is not None:
        kvn_path = working_dir.joinpath(path)
        if not working_dir.joinpath(kvn_path).exists():
            kvn_path = working_dir.joinpath(extra_path).joinpath(path)

        # read KVN file
        ndm = NdmKvnIo().from_path(kvn_path)

        # read equivalent XML file
        ndm_truth = NdmIo().from_path(kvn_path.with_suffix(".xml"))

        # export both files to kml and compare
        xml_text = NdmIo().to_string(ndm, NDMFileFormats.XML)
        xml_text_truth = NdmIo().to_string(ndm_truth, NDMFileFormats.XML)

        # NdmIo().to_file(
        #     ndm, working_dir.joinpath(Path("data", "kvn", "deneme_cdm.xml"))
        # )
        # NdmIo().to_file(
        #     ndm,
        #     working_dir.joinpath(Path("data", "kvn", "deneme_cdm_truth.xml")),
        # )

        # compare strings
        assert xml_text_truth == xml_text
