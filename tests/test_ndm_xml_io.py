# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations for XML.

"""

from pathlib import Path

import pytest

from ccsds_ndm.models.ndmxml2 import Omm
from ccsds_ndm.ndm_xml_io import NdmXmlIo
from tests.test_ndm_io import process_paths

xml_file_paths = {
    "AEMv1": Path("data", "xml", "NDMXML-P1.0.1-figure-B-2.xml"),
    "APMv1": Path("data", "xml", "NDMXML-P1.0.1-figure-B-3.xml"),
    "CDMv1": Path("data", "xml", "cdm_example_section4.xml"),
    "OEMv2": Path("data", "xml", "ndmxml-1.0-oem-2.0-single.xml"),
    "OMMv2": Path("data", "xml", "ndmxml-1.0-omm-2.0.xml"),
    "OPMv2": None,
    "RDMv1": None,
    "TDMv1": Path("data", "xml", "tdm-testcase01a-fordocument.xml"),
    "TDMv2": Path("data", "xml", "CCSDS 503.0-B-2_fig E-21.xml"),
    "NDMv2": Path("data", "xml", "omm_combined.xml"),
    "NDMv2_strip": Path("data", "xml", "omm_single_ndm.xml"),
}


# This is for temporary tests only
def test_read_single_file():
    """Tests reading NDM files."""

    path = Path("data", "xml", "omm_combined.xml")

    # *** read XML files ***
    # *** should raise an error in case something goes wrong ***
    if path:
        xml_path = process_paths(Path.cwd(), path)

        # try a string rather than a path
        NdmXmlIo().from_path(str(xml_path))


@pytest.mark.parametrize("ndm_key, path", xml_file_paths.items())
def test_read_files(ndm_key, path):
    """Tests reading NDM files."""

    # *** read XML files ***
    # *** should raise an error in case something goes wrong ***
    if path is not None:
        xml_path = process_paths(Path.cwd(), path)

        # try a string rather than a path
        NdmXmlIo().from_path(str(xml_path))


def test_strip_ndm_combi():
    """Tests stripping the single instantiation from the NDM
    Combined Instantiation file."""

    # *** read XML file ***
    path = xml_file_paths["NDMv2_strip"]
    xml_path = process_paths(Path.cwd(), path)

    omm = NdmXmlIo().from_path(xml_path)

    # End result should be an OMM file, not NDM
    # File is OMM v2, which uses NDM v2
    assert isinstance(omm, Omm)


@pytest.mark.parametrize("ndm_key", ["APMv1", "NDMv2"])
def test_read_string_and_bytes(ndm_key):
    """Tests reading XML data as string and bytes."""

    # check path and correct if necessary
    xml_path_ndm = process_paths(Path.cwd(), xml_file_paths[ndm_key])

    # read XML file as text
    NdmXmlIo().from_string(xml_path_ndm.read_text())

    # read XML file as bytes
    NdmXmlIo().from_bytes(xml_path_ndm.read_bytes())

    # read XML file as bytes from top level interface
    NdmXmlIo().from_bytes(xml_path_ndm.read_bytes())


@pytest.mark.parametrize("ndm_key, path", xml_file_paths.items())
def test_write_string(ndm_key, path):
    """Tests writing XML data as string."""

    # *** read XML files ***
    # *** should raise an error in case something goes wrong ***
    if path is not None:
        xml_path = process_paths(Path.cwd(), path)

        # read XML file into object and write to string
        ndm = NdmXmlIo().from_path(xml_path)
        xml_text_out = NdmXmlIo().to_string(ndm)

        # print(xml_text_out)

        # round-trip: parse the written string back and compare objects
        ndm_readback = NdmXmlIo().from_string(xml_text_out)
        assert ndm == ndm_readback


def test_write_file():
    """Tests writing XML data as file."""

    # check path and correct if necessary
    xml_read_path = process_paths(Path.cwd(), xml_file_paths["TDMv2"])
    xml_write_path = xml_read_path.parent / "write_test.xml"

    # read XML file into object and write to file
    ndm = NdmXmlIo().from_path(xml_read_path)
    NdmXmlIo().to_file(
        ndm,
        xml_write_path,
    )

    # round-trip: read written file back and compare objects
    ndm_readback = NdmXmlIo().from_path(xml_write_path)
    assert ndm == ndm_readback

    # clean up the written file
    xml_write_path.unlink()
