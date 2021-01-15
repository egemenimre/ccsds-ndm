# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages XML File I/O.

"""

from enum import Enum, auto
from pathlib import Path

from ccsds_ndm.ndm_kvn_io import NdmKvnIo
from ccsds_ndm.ndm_xml_io import NdmXmlIo


class NDMFileFormats(Enum):
    """
    NDM file formats.
    """

    XML = auto()
    KVN = auto()
    JSON = auto()


class NdmIo:
    """
    Unified I/O Model for CCSDS Navigation Data Message (NDM) input and output.
    """

    def from_path(self, input_file_path):
        """
        Reads the file to extract contents to an object of correct type.

        Parameters
        ----------
        input_file_path : Path or AnyStr
            Path of the file to be read (path or pathlike accepted)

        Returns
        -------
        object
            NDM Object tree from the file contents
        """
        # read file contents as text
        file_contents = Path(input_file_path).read_text()

        # parse as `from_string()`
        return self.from_string(file_contents)

    def from_bytes(self, ndm_data_source):
        """
        Reads the input bytes array to extract contents to an object of correct type.

        Parameters
        ----------
        ndm_data_source : bytes
            NDM data as input bytes array

        Returns
        -------
        object
            NDM Object tree from the file contents
        """
        # decode bytes and parse as `from_string()`
        return self.from_string(ndm_data_source.decode())

    def from_string(self, ndm_data_source):
        """
        Reads the input string to extract contents to an object of correct type.

        Parameters
        ----------
        ndm_data_source : str
            input string data

        Raises
        ------
        NotImplementedError
            JSON input not implemented in CCSDS NDM Standard yet.

        Returns
        -------
        object
            NDM Object tree from the file contents
        """
        # Identify data format
        data_format = _identify_data_format(ndm_data_source)

        if data_format is NDMFileFormats.XML:
            return NdmXmlIo().from_string(ndm_data_source)

        if data_format is NDMFileFormats.KVN:
            return NdmKvnIo().from_string(ndm_data_source)

        if data_format is NDMFileFormats.JSON:
            raise NotImplementedError(
                "JSON input has not been defined in the CCSDS standard."
            )
        else:
            raise ValueError(
                "NDM Data type could not be identified (valid formats: KVN, XML or JSON)"
            )

    def to_string(self, ndm_obj, data_format, **kwargs):
        """
        Convert and return the given object tree as xml string.

        Parameters
        ----------
        ndm_obj
            input object tree
        data_format : NDMFileFormats
            output data format (KVN, XML or JSON)
        kwargs
            other keywords to be passed on to individual writers
            (e.g. `schema_location` and `no_namespace_schema_location`
            for XML output)

        Returns
        -------
        str
            given object tree as string in the requested format
        """
        if data_format is NDMFileFormats.XML:
            return NdmXmlIo().to_string(ndm_obj, **kwargs)

        if data_format is NDMFileFormats.KVN:
            return NdmKvnIo().to_string(ndm_obj)

        if data_format is NDMFileFormats.JSON:
            raise NotImplementedError(
                "JSON input has not been defined in the CCSDS standard."
            )

    def to_file(self, ndm_obj, data_format, xml_write_file_path, **kwargs):
        """
        Convert and return the given object tree as output file.

        Parameters
        ----------
        ndm_obj
            input object tree
        data_format : NDMFileFormats
            output data format (KVN, XML or JSON)
        xml_write_file_path : Path or AnyStr
            Path of the file to be written (path or pathlike accepted)
        kwargs
            other keywords to be passed on to individual writers
            (e.g. `schema_location` and `no_namespace_schema_location`
            for XML output)

        """
        if data_format is NDMFileFormats.XML:
            return NdmXmlIo().to_file(ndm_obj, xml_write_file_path, **kwargs)

        if data_format is NDMFileFormats.KVN:
            return NdmKvnIo().to_file(ndm_obj, xml_write_file_path)

        if data_format is NDMFileFormats.JSON:
            raise NotImplementedError(
                "JSON input has not been defined in the CCSDS standard."
            )


def _identify_data_format(ndm_data_source):
    """
    Identify the data format of the input string.

    Parameters
    ----------
    ndm_data_source: str
        NDM data as string

    Raises
    ------
    ValueError
        Data format not recognised.

    Returns
    -------
    NDMFileFormats
        Data format (KVN, XML or JSON)
    """
    stripped_source = ndm_data_source.strip()
    if stripped_source.startswith("CCSDS_"):
        file_format = NDMFileFormats.KVN
    elif stripped_source.startswith("<") and stripped_source.endswith(">"):
        file_format = NDMFileFormats.XML
    elif stripped_source.startswith("[") and stripped_source.endswith("]"):
        file_format = NDMFileFormats.JSON
    else:
        raise ValueError(
            "Data type could not be identified (valid formats: KVN, XML or JSON)"
        )
    return file_format
