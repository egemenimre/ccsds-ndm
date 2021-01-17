# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2021 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations for the top level wrapper.

"""
from pathlib import Path

import pytest

from ccsds_ndm.ndm_io import NdmIo, NDMFileFormats

extra_path = Path("ccsds_ndm", "tests")

file_paths = {
    "AEMv1": Path("data", "xml", "NDMXML-P1.0.1-figure-B-2.xml"),
    "APMv1": Path("data", "xml", "NDMXML-P1.0.1-figure-B-3.xml"),
    "CDMv1": Path("data", "kvn", "cdm_example_section4.kvn"),
    "OEMv1": str(Path("data", "xml", "ndmxml-1.0-oem-2.0-single.xml")),
    "OMMv1_1": Path("data", "kvn", "omm1_st.kvn"),
    "OMMv1_2": str(Path("data", "kvn", "omm1_ct.kvn")),
    "OMMv1": Path("data", "xml", "ndmxml-1.0-omm-2.0.xml"),
    "OPMv1": None,
    "RDMv1": None,
    "TDMv1": Path("data", "xml", "tdm-testcase01a-fordocument.xml"),
    "NDMv1": Path("data", "xml", "omm_combined.xml"),
    "NDMv1_strip": Path("data", "xml", "omm_single_ndm.xml"),
}
wrong_contents = [
    "THIS=is a wrong data \n More wrong data\n",
    "<THIS=is a wrong data \n More wrong data>\n",
]

not_implemented = {
    "OMMv1_1": Path("data", "json", "omm1_st.json"),
    "OMMv1_2": str(Path("data", "json", "omm1_ct.json")),
}


@pytest.mark.parametrize("ndm_key, path", file_paths.items())
def test_read_files(ndm_key, path):
    """Tests reading NDM files."""

    # *** read files ***
    # *** should raise an error in case something goes wrong ***
    if path is not None:
        xml_path = Path.cwd().joinpath(path)
        if not Path.cwd().joinpath(xml_path).exists():
            xml_path = Path.cwd().joinpath(extra_path).joinpath(path)

        # try a string rather than a path
        NdmIo().from_path(xml_path)


@pytest.mark.parametrize("source_data", wrong_contents)
def test_read_errs(source_data):
    with pytest.raises(ValueError) as exc_info:
        # this should throw an ValueError exception
        NdmIo().from_string(source_data)


@pytest.mark.parametrize("ndm_key, path", not_implemented.items())
def test_read_json_file(ndm_key, path):
    with pytest.raises(NotImplementedError) as exc_info:

        # *** read files ***
        # *** should raise an error in case something goes wrong ***
        if path is not None:
            json_path = Path.cwd().joinpath(path)
            if not Path.cwd().joinpath(json_path).exists():
                json_path = Path.cwd().joinpath(extra_path).joinpath(path)

            # this should throw an NotImplementedError exception
            NdmIo().from_path(json_path)


def test_write_kvn_string():
    """Tests writing KVN data as string."""
    with pytest.raises(NotImplementedError) as exc_info:
        # check path and correct if necessary
        kvn_path = Path.cwd().joinpath(not_implemented.get("OMMv1_1"))
        if not Path.cwd().joinpath(kvn_path).exists():
            kvn_path = (
                Path.cwd().joinpath(extra_path).joinpath(not_implemented.get("OMMv1_1"))
            )

        # read KVN file
        ndm = NdmIo().from_path(kvn_path)

        # read equivalent XML file
        ndm_truth = NdmIo().from_path(kvn_path.with_suffix(".xml"))

        # export both files to KVN and compare
        kvn_text = NdmIo().to_string(ndm, NDMFileFormats.KVN)
        kvn_text_truth = NdmIo().to_string(ndm_truth, NDMFileFormats.KVN)

        # compare strings
        assert kvn_text_truth == kvn_text


def test_write_json_string():
    """Tests writing JSON data as string."""
    with pytest.raises(NotImplementedError) as exc_info:
        # check path and correct if necessary
        kvn_path = Path.cwd().joinpath(file_paths.get("OMMv1_1"))
        if not Path.cwd().joinpath(kvn_path).exists():
            kvn_path = (
                Path.cwd().joinpath(extra_path).joinpath(file_paths.get("OMMv1_1"))
            )

        # read KVN file
        ndm = NdmIo().from_path(kvn_path)

        # read equivalent JSON file
        ndm_truth = NdmIo().from_path(kvn_path.with_suffix(".xml"))

        # export both files to JSON and compare
        kvn_text = NdmIo().to_string(ndm, NDMFileFormats.JSON)
        kvn_text_truth = NdmIo().to_string(ndm_truth, NDMFileFormats.JSON)

        # compare strings
        assert kvn_text_truth == kvn_text
