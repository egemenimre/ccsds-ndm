# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages KVN File I/O.

Entry point for reading KVN-formatted NDM files.  Parsing is a three-step
pipeline:

1. **Tokenise** (``kvn_utils_tokenizer.tokenize``) — every input line is classified
   into a :class:`~ccsds_ndm.kvn_utils_tokenizer.KvnLine` subclass
   (``KvLine``, ``CommentLine``, ``PackedDataLine``, etc.).

2. **Block-split** (``kvn_utils_parser.parse_blocks``) — the token list is
   driven through a state machine that groups lines into
   :class:`~ccsds_ndm.kvn_utils_parser.KvnBlock` objects and wraps them in a
   :class:`~ccsds_ndm.kvn_utils_parser.KvnDocument` together with the detected
   NDM type.

3. **Object construction** — the ``KvnDocument`` is mapped onto the
   xsdata-generated dataclass tree for the identified NDM type.
"""

from pathlib import Path

from ccsds_ndm.kvn_utils_builder import build_object
from ccsds_ndm.kvn_utils_parser import KvnDocument, parse_blocks
from ccsds_ndm.kvn_utils_tokenizer import KvnLine, tokenize


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

        # Step 1: classify every input line into a typed KvnLine subclass
        _lines: list[KvnLine] = tokenize(kvn_source)

        # Step 2: group lines into header + ordered KvnBlocks and resolve the NDM type
        _doc: KvnDocument = parse_blocks(_lines)

        # Step 3: map the KvnDocument onto the xsdata dataclass tree
        return build_object(_doc)
