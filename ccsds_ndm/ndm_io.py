# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 Egemen Imre
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

from ccsds_ndm.ndmxml1 import Aem, Apm, Cdm, Ndm, Oem, Omm, Opm, Rdm, Tdm


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
        ndm_data_type
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

    def __strip_multi_ndm(self, ndm):
        """
        Identifies whether the Combined Instantiation NDM actually contains
        a single element (OMM, APM etc.) with a single member and,
        if so, returns this element. Otherwise returns this Combined
        Instantiation NDM.

        Returns
        -------
        ndm_elem : NDM element
            Identified and stripped NDM element or the original Combi-NDM
        """
        # Find the elements that have non-zero members (omit the "comment" tag)
        non_zero_elem_list = list(
            filter(
                lambda elem: len(vars(ndm)[elem]) > 0 and elem != "comment", vars(ndm)
            )
        )

        if len(non_zero_elem_list) == 1:
            # single element available, check number of members
            ndm_elem = vars(ndm)[non_zero_elem_list[0]]
            if len(ndm_elem) == 1:
                # single element available, return it
                return ndm_elem[0]
            # multiple elements available, return them
            return ndm
        else:
            # multiple elements available, return them
            return ndm

    def from_path(self, xml_read_file_path):
        """
        Reads the file to extract contents to an object of correct type.

        Parameters
        ----------
        xml_read_file_path : Path
            Path of the XML file to be read

        Returns
        -------
        object
            Object tree from the file contents
        """
        ndm_combi = False
        # Identify the data type of the file
        try:
            root = ElementTree.parse(xml_read_file_path).getroot()
            data_type = _NdmDataType.find_element(root.attrib.get("id")).clazz
        except ElementTree.ParseError:
            # auto identify failed, try NDM (Combined Instantiation)
            data_type = Ndm
            ndm_combi = True

        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        # parse file
        ndm = self.parser.from_path(xml_read_file_path, data_type)

        if ndm_combi is False:
            # Usual single element file
            return ndm
        else:
            # File is NDM Combined Instantiation
            # If it actually has a single element, strip the ndm tags
            return self.__strip_multi_ndm(ndm)

    def from_bytes(self, xml_source):
        """
        Reads the input bytes array to extract contents to an object of correct type.

        Parameters
        ----------
        xml_source : bytes
            input bytes array

        Returns
        -------
        object
            Object tree from the file contents
        """
        ndm_combi = False
        # Identify data type of the bytes
        try:
            root = ElementTree.XML(xml_source)
            data_type = _NdmDataType.find_element(root.attrib.get("id")).clazz
        except ElementTree.ParseError:
            # auto identify failed, try NDM (Combined Instantiation)
            data_type = Ndm
            ndm_combi = True

        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        ndm = self.parser.from_bytes(xml_source, data_type)

        if ndm_combi is False:
            # Usual single element file
            return ndm
        else:
            # File is NDM Combined Instantiation
            # If it actually has a single element, strip the ndm tags
            return self.__strip_multi_ndm(ndm)

    def from_string(self, xml_source):
        """
        Reads the input string to extract contents to an object of correct type.

        Parameters
        ----------
        xml_source : str
            input bytes array

        Returns
        -------
        object
            Object tree from the file contents
        """
        ndm_combi = False
        # Identify data type of the string
        try:
            root = ElementTree.XML(xml_source)
            data_type = _NdmDataType.find_element(root.attrib.get("id")).clazz
        except ElementTree.ParseError:
            # auto identify failed, try NDM (Combined Instantiation)
            data_type = Ndm
            ndm_combi = True

        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        ndm = self.parser.from_string(xml_source, data_type)

        if ndm_combi is False:
            # Usual single element file
            return ndm
        else:
            # File is NDM Combined Instantiation
            # If it actually has a single element, strip the ndm tags
            return self.__strip_multi_ndm(ndm)

    def to_string(self, ndm_obj):
        """
        Convert and return the given object tree as xml string.

        Parameters
        ----------
        ndm_obj
            input object tree

        Returns
        -------
        str
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
        """
        xml_txt = self.to_string(ndm_obj)
        xml_write_file_path.write_text(xml_txt)
