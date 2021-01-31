# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2021 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages XML File I/O.

"""

import xml.etree.ElementTree as ElementTree
from enum import Enum
from pathlib import Path

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from ccsds_ndm.models.ndmxml2 import Aem, Apm, Cdm, Ndm, Oem, Omm, Opm, Rdm, Tdm


class _NdmDataType(Enum):
    """
    NDM Data Type (e.g. OEM or AEM).
    """

    AEMv2 = (Aem.Meta.name, Aem)
    APMv2 = (Apm.Meta.name, Apm)
    CDMv2 = (Cdm.Meta.name, Cdm)
    OEMv2 = (Oem.Meta.name, Oem)
    OMMv2 = (Omm.Meta.name, Omm)
    OPMv2 = (Opm.Meta.name, Opm)
    RDMv2 = (Rdm.Meta.name, Rdm)
    TDMv2 = (Tdm.Meta.name, Tdm)

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
            NDM data id (e.g. `aem` or `ndm`)
        Returns
        -------
        ndm_data_type
            correct `_NdmDataType` enum corresponding to the id
        """
        for ndm_data in _NdmDataType:
            if ndm_data.ndm_id == ndm_id:
                return ndm_data


class NdmXmlIo:
    """
    Unified I/O Model for XML input and output.
    """

    def __init__(self):
        self.parser = None
        self.serializer = None

    def from_path(self, xml_read_file_path):
        """
        Reads the file to extract contents to an object of correct type.

        Parameters
        ----------
        xml_read_file_path : Path or AnyStr
            Path of the XML file to be read

        Returns
        -------
        object
            Object tree from the file contents
        """
        # read file contents as text
        file_contents = Path(xml_read_file_path).read_text()

        # parse as `from_string()`
        return self.from_string(file_contents)

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
        # decode bytes and parse as `from_string()`
        return self.from_string(xml_source.decode())

    def from_string(self, xml_source):
        """
        Reads the input string to extract contents to an object of correct type.

        Parameters
        ----------
        xml_source : str
            input string data

        Returns
        -------
        object
            Object tree from the file contents
        """
        # lazy init parser
        if self.parser is None:
            self.__init_parser()

        # Identify data type of the string (Oem, Apm etc.)
        data_type, ndm_combi = _identify_data_type(xml_source)

        ndm = self.parser.from_string(xml_source)

        # if the file is NDM, downcast the elements to their respective subclasses
        if isinstance(ndm, Ndm):
            for tag, ndm_item_list in vars(ndm).items():
                if tag == "comment" or tag == "message_id":
                    continue
                for i, ndm_item in enumerate(ndm_item_list):
                    subclazz = type(ndm_item).__subclasses__()[0]
                    ndm_item.__class__ = subclazz

        if ndm_combi is False:
            # Usual single element file
            return ndm
        else:
            # File is NDM Combined Instantiation
            # If it actually has a single element, strip the ndm tags
            return _strip_multi_ndm(ndm)

    def to_string(
        self, ndm_obj, schema_location=None, no_namespace_schema_location=None
    ):
        """
        Convert and return the given object tree as xml string.

        Parameters
        ----------
        ndm_obj
            input object tree
        schema_location: str
            Specify the xsi:schemaLocation attribute value
        no_namespace_schema_location: str
            Specify the xsi:noNamespaceSchemaLocation attribute value

        Returns
        -------
        str
            given object tree as xml string
        """
        # lazy init serializer
        if self.serializer is None:
            self.__init_serializer(
                no_namespace_schema_location=no_namespace_schema_location,
                schema_location=schema_location,
            )

        return self.serializer.render(ndm_obj)

    def to_file(
        self,
        ndm_obj,
        xml_write_file_path,
        schema_location=None,
        no_namespace_schema_location=None,
    ):
        """
        Convert and return the given object tree as xml file.

        Parameters
        ----------
        ndm_obj
            input object tree
        xml_write_file_path : Path
            Path of the XML file to be written
        schema_location: str
            Specify the xsi:schemaLocation attribute value
        no_namespace_schema_location: str
            Specify the xsi:noNamespaceSchemaLocation attribute value
        """
        xml_txt = self.to_string(
            ndm_obj,
            no_namespace_schema_location=no_namespace_schema_location,
            schema_location=schema_location,
        )
        Path(xml_write_file_path).write_text(xml_txt)

    def __init_parser(self):
        """
        Inits the internal parser.
        """
        config = ParserConfig(fail_on_unknown_properties=True)
        self.parser = XmlParser(config=config)

    def __init_serializer(
        self, schema_location=None, no_namespace_schema_location=None
    ):
        """
        Inits the internal serializer.

        Parameters
        ----------
        schema_location: str
            Specify the xsi:schemaLocation attribute value
        no_namespace_schema_location: str
            Specify the xsi:noNamespaceSchemaLocation attribute value
        """
        config = SerializerConfig(
            pretty_print=True,
            schema_location=schema_location,
            no_namespace_schema_location=no_namespace_schema_location,
        )
        self.serializer = XmlSerializer(config=config)


def _identify_data_type(xml_source):
    """
    Identify the XML data type.

    Parameters
    ----------
    xml_source : str
        NDM Data as XML string

    Returns
    -------
    (data_type, ndm_combi) : (type, bool)
        Identified data type and whether it is a Combined NDM file

    """
    ndm_combi = False
    try:
        if isinstance(xml_source, Path):
            # input is a file
            root = ElementTree.parse(xml_source).getroot()
        else:
            # file is string or bytes
            root = ElementTree.XML(xml_source)
        # find data type
        data_type = _NdmDataType.find_element(root.tag).clazz
    except (ElementTree.ParseError, AttributeError):
        # auto identify failed, try NDM (Combined Instantiation)
        ndm_combi = True
        data_type = Ndm

    return data_type, ndm_combi


def _strip_multi_ndm(ndm):
    """
    Identifies whether the Combined Instantiation NDM actually contains
    a single element (OMM, APM etc.) with a single member and,
    if so, returns this element. Otherwise returns this Combined
    Instantiation NDM.

    Parameters
    ----------
    ndm
        NDM data object

    Returns
    -------
    ndm_elem : NDM element
        Identified and stripped NDM element or the original Combi-NDM
    """
    # Find the elements that have non-zero members (omit the "comment"
    # and "message_id" tags)
    non_zero_elem_list = list(
        filter(
            lambda elem: elem != "message_id"
            and elem != "comment"
            and len(vars(ndm)[elem]) > 0,
            vars(ndm),
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
