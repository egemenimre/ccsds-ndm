# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 CCSDS-NDM Project Team
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages XML File I/O.

"""

import xml.etree.ElementTree as ElementTree
from enum import Enum

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer

from src.examples.xsdata_example.ndmxml1 import (
    Aem,
    Apm,
    Cdm,
    Oem,
    Omm,
    Opm,
    Rdm,
    Tdm,
)


class _NdmDataType(Enum):
    """
    NDM Data Type (e.g. OEM or AEM).
    """

    AEMv1 = (Aem.id, Aem)
    APMv1 = (Apm.id, Apm)
    CDMv1 = (Cdm.id, Cdm)
    OEMv1 = (Oem.id, Oem)
    OMMv1 = (Omm.id, Omm)
    OPMv1 = (Opm.id, Opm)
    RDMv1 = (Rdm.id, Rdm)
    TDMv1 = (Tdm.id, Tdm)

    def __init__(self, ndm_id, clazz):
        self.clazz = clazz
        self.ndm_id = ndm_id

    @staticmethod
    def find_element(ndm_id):
        """
        Finds the NDM Data Type corresponding to the requested id.

        Parameters
        ----------
        ndm_id : str
            NDM data id (e.g. `CCSDS_AEM_VERS`)
        Returns
        -------
        correct `_NdmDataType` enum corresponding to the id
        """
        for ndm_data in _NdmDataType:
            if ndm_data.ndm_id == ndm_id:
                return ndm_data


class NdmIo:
    """
    Navigation Data Message.
    """

    def __init__(self):
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

    @staticmethod
    def __identify_data_type(xml_data):
        """
        Identifies the data type (AEM, CDM etc.) of the XML data.

        Parameters
        ----------
        xml_data
            filename or file object containing XML data
        Returns
        -------
        XML Data class

        """
        # Identify the data type
        root = ElementTree.parse(xml_data).getroot()

        return _NdmDataType.find_element(root.attrib.get("id")).clazz

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
        # Identify data type
        data_type = self.__identify_data_type(xml_read_file_path)

        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        return self.parser.from_path(xml_read_file_path, data_type)

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
        # Identify data type
        data_type = self.__identify_data_type(xml_source)

        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        return self.parser.from_bytes(xml_source, data_type)

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
        # Identify data type
        data_type = self.__identify_data_type(xml_source)

        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        return self.parser.from_string(xml_source, data_type.value)

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
