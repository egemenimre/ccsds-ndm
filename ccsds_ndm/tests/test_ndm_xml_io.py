# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations for XML.

"""

from pathlib import Path

import pytest

from ccsds_ndm.models.ndmxml2 import Omm
from ccsds_ndm.ndm_io import NDMFileFormats, NdmIo
from ccsds_ndm.ndm_xml_io import NdmXmlIo

extra_path = Path("ccsds_ndm", "tests")

xml_file_paths = {
    "AEMv2": Path("data", "xml", "NDMXML-P1.0.1-figure-B-2.xml"),
    "APMv2": Path("data", "xml", "NDMXML-P1.0.1-figure-B-3.xml"),
    "CDMv2": Path("data", "xml", "cdm_example_section4.xml"),
    "OEMv2": Path("data", "xml", "ndmxml-1.0-oem-2.0-single.xml"),
    "OMMv2": Path("data", "xml", "ndmxml-1.0-omm-2.0.xml"),
    "OPMv2": None,
    "RDMv2": None,
    "TDMv2": Path("data", "xml", "tdm-testcase01a-fordocument.xml"),
    "NDMv2": Path("data", "xml", "omm_combined.xml"),
    "NDMv2_strip": Path("data", "xml", "omm_single_ndm.xml"),
}


@pytest.mark.parametrize("ndm_key, path", xml_file_paths.items())
def test_read_files(ndm_key, path):
    """Tests reading NDM files."""

    # *** read XML files ***
    # *** should raise an error in case something goes wrong ***
    if path is not None:
        xml_path = Path.cwd().joinpath(path)
        if not Path.cwd().joinpath(xml_path).exists():
            xml_path = Path.cwd().joinpath(extra_path).joinpath(path)

        # try a string rather than a path
        NdmXmlIo().from_path(str(xml_path))


def test_strip_ndm_combi():
    """Tests stripping the single instantiation from the NDM
    Combined Instantiation file."""

    # *** read XML file ***
    path = xml_file_paths.get("NDMv2_strip")
    xml_path = Path.cwd().joinpath(path)
    if not Path.cwd().joinpath(xml_path).exists():
        xml_path = Path.cwd().joinpath(extra_path).joinpath(path)

    omm = NdmIo().from_path(xml_path)

    # End result should be an OMM file, not NDM
    assert isinstance(omm, Omm)


@pytest.mark.parametrize("ndm_key", ["APMv2", "NDMv2"])
def test_read_string_and_bytes(ndm_key):
    """Tests reading XML data as string and bytes."""

    # check path and correct if necessary
    xml_path_ndm = Path.cwd().joinpath(xml_file_paths.get(ndm_key))
    if not Path.cwd().joinpath(xml_path_ndm).exists():
        xml_path_ndm = (
            Path.cwd().joinpath(extra_path).joinpath(xml_file_paths.get(ndm_key))
        )

    # read XML file as text
    NdmIo().from_string(xml_path_ndm.read_text())

    # read XML file as bytes
    NdmXmlIo().from_bytes(xml_path_ndm.read_bytes())

    # read XML file as bytes from top level interface
    NdmIo().from_bytes(xml_path_ndm.read_bytes())


def _text_to_list(text):
    """Converts text to list."""
    stripped_list = [x.strip() for x in text.split("\n")]
    return [x for x in stripped_list if x]


def test_write_string():
    """Tests writing XML data as string."""

    # check path and correct if necessary
    working_dir = Path.cwd()
    xml_path = working_dir.joinpath(xml_file_paths.get("OEMv2"))
    if not working_dir.joinpath(xml_path).exists():
        working_dir = working_dir.joinpath(extra_path)

    xml_path = working_dir.joinpath(xml_file_paths.get("OEMv2"))

    # read XML file as text
    xml_text = xml_path.read_text()

    # read XML file into object and write to string
    ndm = NdmIo().from_path(xml_path)
    xml_text_out = NdmIo().to_string(ndm, NDMFileFormats.XML)

    # Prepare texts for comparison (convert lines to list, delete empty items)
    xml_text = _text_to_list(xml_text)
    xml_text_out = _text_to_list(xml_text_out)

    # compare strings
    assert xml_text[4:] == xml_text_out[2:]


def test_write_file():
    """Tests writing XML data as file."""

    # check path and correct if necessary
    working_dir = Path.cwd()
    xml_read_path = working_dir.joinpath(xml_file_paths.get("OEMv2"))
    if not working_dir.joinpath(xml_read_path).exists():
        working_dir = working_dir.joinpath(extra_path)

    xml_read_path = working_dir.joinpath(xml_file_paths.get("OEMv2"))

    xml_write_path = working_dir.joinpath(Path("data", "xml", "write_test.xml"))

    # read XML file as text
    xml_text = _text_to_list(xml_read_path.read_text())

    # read XML file into object and write to file
    ndm = NdmIo().from_path(xml_read_path)
    NdmIo().to_file(
        ndm,
        NDMFileFormats.XML,
        xml_write_path,
        no_namespace_schema_location="http://cwe.ccsds.org/moims/docs/MOIMS-NAV/Schemas/ndmxml-1.0-master.xsd",
    )

    # read written XML file as text
    xml_text_out = _text_to_list(xml_write_path.read_text())

    # compare strings
    assert xml_text[4:] == xml_text_out[2:]
