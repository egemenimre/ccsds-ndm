# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 CCSDS-NDM Project Team
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
xsdata example. Uses auto-generated classes from the XSD files.

"""

import os
from builtins import print
from pathlib import Path

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from src.examples.xsdata_example.ndm_io import NdmIo, NdmDataType
from src.examples.xsdata_example.ndmxml1 import Cdm

if __name__ == "__main__":
    # *** print working directory ***
    print(f"current working directory is {os.getcwd()}.")

    # *** check file location ***
    xml_read_file_path = Path(
        os.getcwd(), "..", "..", "sample_xml", "cdm_example_section4.xml"
    )

    print(f"xml file path : {xml_read_file_path.resolve()}")
    print(f"file exists   : {xml_read_file_path.exists()}")

    # *** read XML file ***
    # config = ParserConfig(fail_on_unknown_properties=True)
    # parser = XmlParser(config=config)
    # cdm = parser.from_path(xml_read_file_path, Cdm)
    cdm_data = NdmIo(NdmDataType.CDMv1)
    cdm = cdm_data.from_path(xml_read_file_path)

    print(cdm.body.relative_metadata_data.relative_state_vector.relative_position_n)

    # *** write XML file ***
    xml_write_file_path = Path(os.getcwd(), "..", "..", "sample_xml", "write_cdm.xml")
    cdm_data.to_file(cdm, xml_write_file_path)

    # serializer = XmlSerializer(pretty_print=True)
    # xml = serializer.render(cdm)
    # xml_write_file_path.write_text(xml)

    # *** read written XML file ***
    config = ParserConfig(fail_on_unknown_properties=True)
    parser = XmlParser(config=config)
    cdm = parser.from_path(xml_write_file_path, Cdm)
