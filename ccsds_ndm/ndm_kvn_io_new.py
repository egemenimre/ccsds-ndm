# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages KVN File I/O.

"""

from pathlib import Path

from ccsds_ndm.kvn_utils_new import KvnLine, tokenize


class NdmKvnIo:
    """
    Unified I/O Model for KVN input and output.
    """

    def from_path(self, kvn_read_file_path):
        """
        Reads the file to extract contents to an object of correct type.

        Parameters
        ----------
        kvn_read_file_path : Path
            Path of the KVN file to be read

        Returns
        -------
        object
            Object tree from the file contents
        """
        return self.from_string(Path(kvn_read_file_path).read_text())

    def from_string(self, kvn_source: str):
        """
        Reads the input string to extract contents to an object of correct type.

        Parameters
        ----------
        kvn_source : str
            input string containing KVN data

        Returns
        -------
        object
            Object tree from the file contents
        """

        # Step 1: tokenise every line into a KvnLine subclass instance
        _lines: list[KvnLine] = tokenize(kvn_source)

        # Step 2: identify the blocks in the KVN data and initialise the xsdata type

        # Step 3: build the object
        return None
