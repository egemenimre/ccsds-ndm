# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 CCSDS-NDM Project Team
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Example with xmlschema library to read and validate XML files.

"""
import os
from builtins import print
from pathlib import Path
from pprint import pprint

import xmlschema

if __name__ == "__main__":
    # print working directory
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"current working directory is {ROOT_DIR}.")

    # check file location
    xml_file_path = Path(ROOT_DIR, "..", "sample_xml", "cdm_example_section4.xml")

    print(f"xml file path : {xml_file_path.resolve()}")
    print(f"file exists   : {xml_file_path.exists()}")

    # define XSD file
    xsd_file_base_path = Path(ROOT_DIR, "..", "..", "xsd_files", "ndmxsd")
    ndm_master_xsd_path = Path(xsd_file_base_path, "ndmxml-1.0-master.xsd")
    # xsd_file_base_path = Path(os.getcwd(), "..", "..", "xsd_files", "ndmxml-2.0.0-schemas-qualified")
    # ndm_master_xsd_path = Path(xsd_file_base_path, "ndmxml-2.0.0-master-2.0.xsd")
    # xsd_file_base_path = Path(os.getcwd(), "..", "..", "xsd_files", "ndmxml-1.0.C-schemas-qualified")
    # ndm_master_xsd_path = Path(xsd_file_base_path, "ndmxml-1.0-master.xsd")

    xsd = xmlschema.XMLSchema(str(ndm_master_xsd_path))

    # read XML file
    print(f"XML is valid  : {xsd.is_valid(xml_file_path.read_text())}")
    # print(xsd.validate(str(xml_file_path)))
    xml_dict = xsd.to_dict(xml_file_path.read_text(), validation="lax")
    pprint(xml_dict)
