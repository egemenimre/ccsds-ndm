# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.

from pathlib import Path

from ccsds_ndm.mapping import NDMFileFormats
from ccsds_ndm.ndm_kvn_io import NdmKvnIo
from ccsds_ndm.ndm_xml_io import NdmXmlIo


class NdmIo:
    """
    Format-agnostic read/write facade for CCSDS Navigation Data Messages.

    Detects whether the source is KVN or XML by inspecting the first
    non-whitespace characters, then delegates to
    :class:`~ccsds_ndm.ndm_kvn_io_new.NdmKvnIo` or
    :class:`~ccsds_ndm.ndm_xml_io.NdmXmlIo` accordingly.

    JSON is not yet defined by the CCSDS standard and will raise
    :exc:`NotImplementedError` if attempted.
    """

    def from_path(self, input_file_path):
        """
        Read an NDM file and return the corresponding object tree.

        Reads the file as plain text and forwards the content to
        :meth:`from_string`, which handles format detection.

        Parameters
        ----------
        input_file_path : Path or str
            Path to the KVN or XML input file.

        Returns
        -------
        object
            Root xsdata dataclass instance for the detected NDM type
            (e.g. ``OpmType``, ``OemType``, ``ApmType``, …).
        """
        file_contents = Path(input_file_path).read_text()
        return self.from_string(file_contents)

    def from_bytes(self, ndm_data_source):
        """
        Read an NDM byte string and return the corresponding object tree.

        Decodes the bytes as UTF-8 and forwards the result to
        :meth:`from_string`, which handles format detection.

        Parameters
        ----------
        ndm_data_source : bytes
            KVN or XML content encoded as a byte string.

        Returns
        -------
        object
            Root xsdata dataclass instance for the detected NDM type
            (e.g. ``OpmType``, ``OemType``, ``ApmType``, …).
        """
        return self.from_string(ndm_data_source.decode())

    def from_string(self, ndm_data_source):
        """
        Parse an NDM string and return the corresponding object tree.

        Calls :func:`_identify_data_format` to determine whether the input
        is KVN or XML, then dispatches to the appropriate parser:

        - **KVN** → :class:`~ccsds_ndm.ndm_kvn_io_new.NdmKvnIo`
        - **XML** → :class:`~ccsds_ndm.ndm_xml_io.NdmXmlIo`

        Parameters
        ----------
        ndm_data_source : str
            Raw KVN or XML text (Windows or Unix line endings accepted).

        Returns
        -------
        object
            Root xsdata dataclass instance for the detected NDM type
            (e.g. ``OpmType``, ``OemType``, ``ApmType``, …).

        Raises
        ------
        NotImplementedError
            If the input is identified as JSON, which is not yet defined
            by the CCSDS NDM standard.
        ValueError
            If the format cannot be identified from the input text.
        """
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
        Serialise an NDM object tree to a string.

        Dispatches to the appropriate writer based on *data_format*:

        - **XML** → :class:`~ccsds_ndm.ndm_xml_io.NdmXmlIo`
        - **KVN** → :class:`~ccsds_ndm.ndm_kvn_io_new.NdmKvnIo`

        Parameters
        ----------
        ndm_obj : object
            Root xsdata dataclass instance to serialise.
        data_format : NDMFileFormats
            Target output format (``NDMFileFormats.KVN`` or ``NDMFileFormats.XML``).
        **kwargs
            Additional keyword arguments forwarded to the underlying writer.
            For XML output: ``schema_location``, ``no_namespace_schema_location``.

        Returns
        -------
        str
            The serialised NDM text in the requested format.

        Raises
        ------
        NotImplementedError
            If *data_format* is ``NDMFileFormats.JSON``.
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
        Serialise an NDM object tree and write it to a file.

        Dispatches to the appropriate writer based on *data_format*:

        - **XML** → :class:`~ccsds_ndm.ndm_xml_io.NdmXmlIo`
        - **KVN** → :class:`~ccsds_ndm.ndm_kvn_io_new.NdmKvnIo`

        Parameters
        ----------
        ndm_obj : object
            Root xsdata dataclass instance to serialise.
        data_format : NDMFileFormats
            Target output format (``NDMFileFormats.KVN`` or ``NDMFileFormats.XML``).
        xml_write_file_path : Path or str
            Destination file path.
        **kwargs
            Additional keyword arguments forwarded to the underlying writer.
            For XML output: ``schema_location``, ``no_namespace_schema_location``.

        Raises
        ------
        NotImplementedError
            If *data_format* is ``NDMFileFormats.JSON``.
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
