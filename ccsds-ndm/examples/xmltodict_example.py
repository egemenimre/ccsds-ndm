# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 CCSDS-NDM Project Team
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
xmltodict example.

"""
import os
from builtins import print
from pathlib import Path
from pprint import pprint

import xmltodict

if __name__ == '__main__':
    # print working directory
    print(f"current working directory is {os.getcwd()}.")

    # check file location
    xml_file_path = Path(os.getcwd(), "..", "sample_xml",
                         "CH_FDS_ORBPRE_OPER_20180320224847_20190601000000_20190608000000.xml")

    print(f"xml file path :  {xml_file_path.resolve()}")
    print(f"file exists   : {xml_file_path.exists()}")

    # read XML file
    pprint(xmltodict.parse(xml_file_path.read_text()))
