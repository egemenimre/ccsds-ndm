# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations.

"""

from pathlib import Path

from ccsds_ndm.ndm_io import NdmIo

extra_path = Path("ccsds_ndm", "tests")

xml_file_paths = {
    "AEMv1": None,
    "APMv1": Path("data", "NDMXML-P1.0.1-figure-B-3.xml"),
    "CDMv1": Path("data", "cdm_example_section4.xml"),
    "OEMv1": Path("data", "ndmxml-1.0-oem-2.0-single.xml"),
    "OMMv1": Path("data", "ndmxml-1.0-omm-2.0.xml"),
    "OPMv1": None,
    "RDMv1": None,
    "TDMv1": None,
    "NDMv1": Path("data", "omm_combined.xml"),
}


def test_read_files():
    """Tests reading NDM files."""

    # *** read XML files ***
    # *** should raise an error in case something goes wrong ***
    for ndm_key, path in xml_file_paths.items():
        if path is not None:
            xml_path = Path.cwd().joinpath(path)
            if not Path.cwd().joinpath(xml_path).exists():
                xml_path = Path.cwd().joinpath(extra_path).joinpath(path)

            NdmIo().from_path(xml_path)


def test_read_string_and_bytes():
    """Tests reading XML data as string and bytes."""

    # check path and correct if necessary
    xml_path_apm = Path.cwd().joinpath(xml_file_paths.get("APMv1"))
    if not Path.cwd().joinpath(xml_path_apm).exists():
        xml_path_apm = (
            Path.cwd().joinpath(extra_path).joinpath(xml_file_paths.get("APMv1"))
        )

    xml_path_ndm = Path.cwd().joinpath(xml_file_paths.get("NDMv1"))
    if not Path.cwd().joinpath(xml_path_ndm).exists():
        xml_path_ndm = (
            Path.cwd().joinpath(extra_path).joinpath(xml_file_paths.get("NDMv1"))
        )

    # read XML file as text
    NdmIo().from_string(xml_path_apm.read_text())
    NdmIo().from_string(xml_path_ndm.read_text())

    # read XML file as bytes
    NdmIo().from_bytes(xml_path_apm.read_bytes())
    NdmIo().from_bytes(xml_path_ndm.read_bytes())


def __text_to_list(text):
    """Converts text to list."""
    stripped_list = [x.strip() for x in text.split("\n")]
    return [x for x in stripped_list if x]


def test_write_string():
    """Tests writing XML data as string."""

    # check path and correct if necessary
    working_dir = Path.cwd()
    xml_path = working_dir.joinpath(xml_file_paths.get("OEMv1"))
    if not working_dir.joinpath(xml_path).exists():
        working_dir = working_dir.joinpath(extra_path)

    xml_path = working_dir.joinpath(xml_file_paths.get("OEMv1"))

    # read XML file as text
    xml_text = xml_path.read_text()

    # read XML file into object and write to string
    ndm = NdmIo().from_path(xml_path)
    xml_text_out = NdmIo().to_string(ndm)

    # Prepare texts for comparison (convert lines to list, delete empty items)
    xml_text = __text_to_list(xml_text)
    xml_text_out = __text_to_list(xml_text_out)

    # compare strings
    assert xml_text[4:] == xml_text_out[2:]


def test_write_file():
    """Tests writing XML data as file."""

    # check path and correct if necessary
    working_dir = Path.cwd()
    xml_read_path = working_dir.joinpath(xml_file_paths.get("OEMv1"))
    if not working_dir.joinpath(xml_read_path).exists():
        working_dir = working_dir.joinpath(extra_path)

    xml_read_path = working_dir.joinpath(xml_file_paths.get("OEMv1"))

    xml_write_path = working_dir.joinpath(Path("data", "write_test.xml"))

    # read XML file as text
    xml_text = __text_to_list(xml_read_path.read_text())

    # read XML file into object and write to file
    ndm = NdmIo().from_path(xml_read_path)
    NdmIo().to_file(ndm, xml_write_path)

    # read written XML file as text
    xml_text_out = __text_to_list(xml_write_path.read_text())

    # compare strings
    assert xml_text[4:] == xml_text_out[2:]
