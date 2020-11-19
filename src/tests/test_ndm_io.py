# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Tests for the NDM File I/O Operations.

"""
import os
from pathlib import Path

from src.ndm_io import NdmIo

working_dir = os.getcwd()

xml_file_paths = {
    "AEMv1": None,
    "APMv1": Path(os.getcwd(), "data", "NDMXML-P1.0.1-figure-B-3.xml"),
    "CDMv1": Path(os.getcwd(), "data", "cdm_example_section4.xml"),
    "OEMv1": Path(os.getcwd(), "data", "ndmxml-1.0-oem-2.0-single.xml"),
    "OMMv1": Path(os.getcwd(), "data", "ndmxml-1.0-omm-2.0.xml"),
    "OPMv1": None,
    "RDMv1": None,
    "TDMv1": None,
}


def test_read_files():
    """Tests reading NDM files."""

    # *** read XML files ***
    # *** should raise an error in case something goes wrong ***
    for ndm_key, path in xml_file_paths.items():
        if path is not None:
            NdmIo().from_path(path)
