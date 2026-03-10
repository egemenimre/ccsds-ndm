# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages XML File I/O.

"""

from pathlib import Path

from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from ccsds_ndm.mapping import _NdmDataType


class NdmXmlIo:
    """
    Unified I/O Model for XML input and output.
    """

    def __init__(self):
        self.parser = None
        self.parser_config = ParserConfig(fail_on_unknown_properties=True)
        self.serializer = None

    def from_path(self, xml_read_file_path: Path | str):
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

    def from_bytes(self, xml_source: bytes):
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

    def from_string(self, xml_source: str):
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
            self.parser = self._init_parser(self.parser_config)

        # Identify data type of the string (Oem, Apm etc.) and parse the data
        # Also overwrite the xml_source with the fixed one from lxml
        data_type, xml_source = self._identify_data_type(xml_source)

        ndm = self.parser.from_string(xml_source, data_type.clazz)

        # if the file is NDM, downcast the elements to their respective subclasses
        if data_type.is_combi:
            for tag, ndm_item_list in vars(ndm).items():
                if tag == "comment" or tag == "message_id":
                    continue
                for ndm_item in ndm_item_list:
                    subclazz = type(ndm_item).__subclasses__()[0]
                    ndm_item.__class__ = subclazz

            # File is NDM Combined Instantiation
            # If it actually has a single element, strip the ndm tags
            return _strip_multi_ndm(ndm)

        else:
            # Usual single element file
            return ndm

    def to_string(
        self,
        ndm_obj,
        schema_location: str | None = None,
        no_namespace_schema_location: str | None = None,
    ) -> str:
        """
        Convert and return the given object tree as xml string.

        Parameters
        ----------
        ndm_obj
            input object tree
        schema_location: str | None
            Specify the xsi:schemaLocation attribute value
        no_namespace_schema_location: str | None
            Specify the xsi:noNamespaceSchemaLocation attribute value

        Returns
        -------
        str
            given object tree as xml string
        """
        # lazy init serializer
        self.serializer = self._init_serializer(
            no_namespace_schema_location=no_namespace_schema_location,
            schema_location=schema_location,
        )

        return self.serializer.render(ndm_obj)

    def to_file(
        self,
        ndm_obj,
        xml_write_file_path: Path,
        schema_location: str | None = None,
        no_namespace_schema_location: str | None = None,
    ):
        """
        Convert the given object tree as xml file.

        Parameters
        ----------
        ndm_obj
            input object tree
        xml_write_file_path : Path
            Path of the XML file to be written
        schema_location: str | None
            Specify the xsi:schemaLocation attribute value
        no_namespace_schema_location: str | None
            Specify the xsi:noNamespaceSchemaLocation attribute value
        """
        xml_txt = self.to_string(
            ndm_obj,
            no_namespace_schema_location=no_namespace_schema_location,
            schema_location=schema_location,
        )
        Path(xml_write_file_path).write_text(xml_txt)

    @staticmethod
    def _identify_data_type(xml_source: str) -> tuple[_NdmDataType, str]:
        """
        Identify the NDM XML data type from an XML string.

        The function parses the XML using lxml.etree with recover=True
        and ns_clean=True to tolerate and clean malformed input.

        Parameters
        ----------
        xml_source : str
            NDM Data as XML string

        Returns
        -------
        data_type : _NdmDataType
            The identified data type (as returned by the _NdmDataType lookup helpers).
        fixed_source : str
            The XML source string, possibly cleaned up by lxml during parsing.

        Behavior / Notes
        ----------------
        - If the root element is "ndm" the function treats the document as a
          Combined NDM file: it skips child elements named "comment" and
          "message_id" and uses the first other child to determine the
          internal data type via _NdmDataType.find_element(child.tag, version),
          then maps that to a combined NDM type via
          _NdmDataType.find_combi_version(...).
        - Otherwise the root element name and its "version" attribute are used
          to lookup the data type via _NdmDataType.find_element(root.tag,
          version).
        """
        parser = etree.XMLParser(recover=True, ns_clean=True)

        # parse the XML string to get the root element
        root = etree.fromstring(xml_source.encode("utf-8"), parser=parser)

        # this can feed the fixed XML back to the parser, if needed. Some files have
        # unescaped characters that cause parsing issues, but can be fixed by
        # lxml's recover mode.
        fixed_xml = etree.tostring(root, pretty_print=True, encoding="unicode")

        if root.tag == "ndm":
            # if the root tag is "ndm", this is a Combined Instantiation file,
            # and we need to look at the children to identify the data type
            # find the first child element that is not "comment" or "message_id"
            for child in root:
                if child.tag != "comment" and child.tag != "message_id":
                    # find data type of the child element
                    ndm_id = child.tag
                    version = child.attrib.get("version")
                    internal_data_type = _NdmDataType.find_ndm_type_by_id(
                        ndm_id, version
                    )

                    # return the first combined NDM version that supports this data type
                    return (
                        _NdmDataType.find_combi_version(internal_data_type),
                        fixed_xml,
                    )

            # Reached here without a valid file inside the NDM Combi
            raise ValueError("No child found in the Combined Instantiation NDM Data.")

        else:
            # This is a usual single element file, the root tag corresponds
            # to the data type

            # find data type
            ndm_id = root.tag
            version = root.attrib.get("version")
            data_type = _NdmDataType.find_ndm_type_by_id(ndm_id, version)

        return data_type, fixed_xml

    @staticmethod
    def _init_parser(config: ParserConfig):
        """
        Inits the internal parser.
        """

        return XmlParser(config=config)

    @staticmethod
    def _init_serializer(
        schema_location: str | None = None,
        no_namespace_schema_location: str | None = None,
    ):
        """
        Inits the internal serializer.

        Parameters
        ----------
        schema_location: str | None
            Specify the xsi:schemaLocation attribute value
        no_namespace_schema_location: str | None
            Specify the xsi:noNamespaceSchemaLocation attribute value
        """
        config = SerializerConfig(
            indent="  ",
            schema_location=schema_location,
            no_namespace_schema_location=no_namespace_schema_location,
        )
        return XmlSerializer(config=config)


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
    non_zero_elem_list = _get_non_zero_elem_names(ndm)

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


# def _is_multi_ndm(ndm) -> bool:
#     """
#     Identifies whether the Combined Instantiation NDM actually contains
#     a single element (OMM, APM etc.) with a single member.

#     Parameters
#     ----------
#     ndm
#         NDM data object

#     Returns
#     -------
#     bool
#         True if this `ndm` is a Combi-NDM, False otherwise.
#     """
#     # Find the elements that have non-zero members (omit the "comment"
#     # and "message_id" tags)
#     non_zero_elem_list = _get_non_zero_elem_names(ndm)

#     if len(non_zero_elem_list) == 1:
#         # single element available, check number of members
#         ndm_elem = vars(ndm)[non_zero_elem_list[0]]
#         if len(ndm_elem) == 1:
#             # single element available, return it
#             return False
#         # multiple elements available, return them
#         return True
#     else:
#         # multiple elements available
#         return True


def _get_non_zero_elem_names(ndm):
    """Return names of ndm attributes that are non-empty, excluding meta fields."""
    return [
        name
        for name, val in vars(ndm).items()
        if name not in ("comment", "message_id") and len(val) > 0
    ]
