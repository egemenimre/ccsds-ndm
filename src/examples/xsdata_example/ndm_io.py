# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 CCSDS-NDM Project Team
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages XML File I/O.

"""

from enum import Enum

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer

from src.examples.xsdata_example.ndmxml1 import (
    Aem,
    Apm,
    Cdm,
    Ndm,
    Oem,
    Omm,
    Opm,
    Rdm,
    Tdm,
)


class NdmDataType(Enum):
    """
    NDM Data Type (e.g. OEM or AEM).
    """

    AEMv1 = Aem
    APMv1 = Apm
    CDMv1 = Cdm
    NDMv1 = Ndm
    OEMv1 = Oem
    OMMv1 = Omm
    OPMv1 = Opm
    RDMv1 = Rdm
    TDMv1 = Tdm

    def __init__(self, clazz):
        self.clazz = clazz


class NdmIo:
    """
    Parameters
    ----------
    data_type : NdmDataType
        NDM data type to be read (e.g. OEMv1 or AEMv1)
    """

    def __init__(self, data_type):
        self.data_type = data_type
        self.parser = None
        self.serializer = None

    def __init_parser(self):
        """
        Inits the internal parser.
        """
        config = ParserConfig(fail_on_unknown_properties=True)
        self.parser = XmlParser(config=config)

    def __init_serializer(self):
        """
        Inits the internal serializer.
        """
        self.serializer = XmlSerializer(pretty_print=True)

    def from_path(self, xml_read_file_path):
        """
        Reads the file to extract contents to an object of correct type.

        Parameters
        ----------
        xml_read_file_path : Path
            Path of the XML file to be read

        Returns
        -------
        Object tree from the file contents
        """
        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        return self.parser.from_path(xml_read_file_path, self.data_type.value)

    def from_bytes(self, xml_source):
        """
        Reads the input bytes array to extract contents to an object of correct type.

        Parameters
        ----------
        xml_source : bytes
            input bytes array

        Returns
        -------
        Object tree from the file contents
        """
        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        return self.parser.from_bytes(xml_source, self.data_type.value)

    def from_string(self, xml_source):
        """
        Reads the input string to extract contents to an object of correct type.

        Parameters
        ----------
        xml_source : str
            input bytes array

        Returns
        -------
        Object tree from the file contents
        """
        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        return self.parser.from_string(xml_source, self.data_type.value)

    def to_string(self, ndm_obj):
        """
        Convert and return the given object tree as xml string.

        Parameters
        ----------
        ndm_obj
            input object tree

        Returns
        -------
        given object tree as xml string
        """
        # lazy init serializer
        if self.serializer is None:
            self.__init_serializer()

        return self.serializer.render(ndm_obj)

    def to_file(self, ndm_obj, xml_write_file_path):
        """
        Convert and return the given object tree as xml file.

        Parameters
        ----------
        ndm_obj
            input object tree
        xml_write_file_path : Path
            Path of the XML file to be written

        Returns
        -------
        given object tree as xml string
        """
        xml_txt = self.to_string(ndm_obj)
        xml_write_file_path.write_text(xml_txt)
