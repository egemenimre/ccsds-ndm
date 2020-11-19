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
from decimal import Decimal
from pathlib import Path

from src.ndm_io import NdmIo
from src.ndmxml1 import LengthType, LengthUnits

# from xsdata.formats.dataclass.parsers import XmlParser
# from xsdata.formats.dataclass.parsers.config import ParserConfig
# from xsdata.formats.dataclass.serializers import XmlSerializer


if __name__ == "__main__":
    # *** print working directory ***
    print(f"current working directory is {os.getcwd()}.")

    # *** check file location ***
    xml_read_file_path = Path(
        os.getcwd(), "..", "sample_xml", "cdm_example_section4.xml"
    )

    print(f"xml file path : {xml_read_file_path.resolve()}")
    print(f"file exists   : {xml_read_file_path.exists()}")

    # *** read XML file ***

    # config = ParserConfig(fail_on_unknown_properties=True)
    # parser = XmlParser(config=config)
    # cdm = parser.from_path(xml_read_file_path, Cdm)
    cdm = NdmIo().from_path(xml_read_file_path)

    # *** Modify object tree ***
    print(cdm.body.relative_metadata_data.relative_state_vector.relative_position_n)

    cdm.body.relative_metadata_data.relative_state_vector.relative_position_n = (
        LengthType(Decimal(800), LengthUnits.M)
    )
    print(cdm.body.relative_metadata_data.relative_state_vector.relative_position_n)

    # *** write XML file ***
    xml_write_file_path = Path(os.getcwd(), "..", "sample_xml", "write_cdm.xml")
    NdmIo().to_file(cdm, xml_write_file_path)

    # serializer = XmlSerializer(pretty_print=True)
    # xml = serializer.render(cdm, ns_map=parser.ns_map)
    # xml_write_file_path.write_text(xml)

    # *** read written XML file ***

    # config = ParserConfig(fail_on_unknown_properties=True)
    # parser = XmlParser(config=config)
    # cdm = parser.from_path(xml_write_file_path, Cdm)
    cdm = NdmIo().from_path(xml_read_file_path)
