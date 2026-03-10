# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages KVN File I/O.

"""

from pathlib import Path

from ccsds_ndm.kvn_builder import build_object
from ccsds_ndm.kvn_parser import dispatch_document
from ccsds_ndm.kvn_tokenizer import tokenize
from ccsds_ndm.kvn_writer import write_kvn_lines
from ccsds_ndm.ndm_utils import is_multi_ndm


class NdmKvnIo:
    """
    KVN read/write facade for CCSDS Navigation Data Messages.

    Delegates the heavy lifting to the pipeline in
    :mod:`ccsds_ndm.kvn_utils_tokenizer` and :mod:`ccsds_ndm.kvn_utils_parser`
    (tokenise → block-split) and then constructs the appropriate xsdata
    dataclass tree.
    """

    def from_path(self, kvn_read_file_path):
        """
        Read a KVN file and return the corresponding NDM object tree.

        Reads the file as plain text and forwards the content to
        :meth:`from_string`.

        Parameters
        ----------
        kvn_read_file_path : Path or str
            Path to the KVN input file.

        Returns
        -------
        object
            Root xsdata dataclass instance for the detected NDM type
            (e.g. ``OpmType``, ``OemType``, ``ApmType``, …).
        """
        return self.from_string(Path(kvn_read_file_path).read_text())

    def from_string(self, kvn_source: str):
        """
        Parse a KVN string and return the corresponding NDM object tree.

        Runs the three-step pipeline described in the module docstring:

        1. :func:`~ccsds_ndm.kvn_utils_tokenizer.tokenize` classifies each line
           into a :class:`~ccsds_ndm.kvn_utils_tokenizer.KvnLine` subclass.
        2. :func:`~ccsds_ndm.kvn_utils_parser.parse_blocks` groups the tokens
           into a :class:`~ccsds_ndm.kvn_utils_parser.KvnDocument` with the NDM
           type resolved from the ``CCSDS_*_VERS`` header line.
        3. The ``KvnDocument`` is mapped onto the xsdata dataclass tree for
           the identified NDM type.

        Parameters
        ----------
        kvn_source : str
            Raw KVN text (Windows or Unix line endings accepted).

        Returns
        -------
        object
            Root xsdata dataclass instance for the detected NDM type
            (e.g. ``OpmType``, ``OemType``, ``ApmType``, …).
        """
        # tokenize the document
        lines = tokenize(kvn_source)

        # dispatch into a KvnDocument with NDM type identified
        kvn_doc = dispatch_document(lines)

        # build the NDM object recursively from the KvnDocument
        return build_object(kvn_doc)

    def to_string(self, ndm_obj) -> str:
        """
        Serialise an xsdata NDM object tree to a KVN string.

        Parameters
        ----------
        ndm_obj : object
            Root xsdata dataclass instance (e.g. ``Opm``, ``Oem``, …).

        Returns
        -------
        str
            The NDM data formatted as a KVN string.

        Raises
        ------
        NotImplementedError
            Combined NDM input for KVN not implemented in CCSDS NDM Standard.
        """
        # check for multi-NDM file
        if is_multi_ndm(ndm_obj):
            raise NotImplementedError(
                "NDM data appears to have more than one data set (e.g. two OPMs). "
                "This sort of NDM output to KVN is not supported. "
                "Try outputting to multiple files instead."
            )

        lines = write_kvn_lines(ndm_obj)
        return "\n".join(line.to_str() for line in lines)

    def to_file(self, ndm_obj, kvn_write_file_path) -> None:
        """
        Serialise an xsdata NDM object tree and write it to a KVN file.

        Parameters
        ----------
        ndm_obj : object
            Root xsdata dataclass instance (e.g. ``Opm``, ``Oem``, …).
        kvn_write_file_path : Path or str
            Destination file path.
        """
        Path(kvn_write_file_path).write_text(self.to_string(ndm_obj))
