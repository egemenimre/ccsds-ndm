# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
KVN block parser: grouping tokenised lines into a :class:`KvnDocument`.

Takes the ordered list of :class:`~ccsds_ndm.kvn_utils_tokenizer.KvnLine`
objects produced by :func:`~ccsds_ndm.kvn_utils_tokenizer.tokenize` and drives
a state machine over them to produce a :class:`KvnDocument` — the fully split
representation of a KVN file ready for object construction.

State machine
-------------
``HEADER``
    Default state.  Lines accumulate in :attr:`KvnDocument.header`.
``IN_META``
    Entered on ``META_START``.  Lines go to :attr:`KvnBlock.meta`.
``AFTER_META``
    Entered on ``META_STOP``.  Used by OEM where raw packed-data lines
    follow the metadata block without an explicit ``DATA_START``.
    Lines go to :attr:`KvnBlock.data`.  On the next ``META_START`` or
    ``COVARIANCE_START`` the open block is flushed to *segments* first.
``IN_DATA``
    Entered on ``DATA_START``.  Lines go to :attr:`KvnBlock.data`.
    Closed by ``DATA_STOP``.
``IN_COVARIANCE``
    Entered on ``COVARIANCE_START``.  A fresh :class:`KvnBlock` is
    opened; lines go to :attr:`KvnBlock.covariance`.  Closed by
    ``COVARIANCE_STOP``.

Flat-type fallback
------------------
If no section markers are encountered (OMM, OPM, APM, RDM, CDM) all lines
after the ``CCSDS_*_VERS`` header line are placed in a single block's
*data* list.

The public entry point is :func:`parse_blocks`.
"""

from dataclasses import dataclass, field

from ccsds_ndm.kvn_utils_tokenizer import KvLine, KvnLine, SectionMarkerLine

# ---------------------------------------------------------------------------
# Block data structures
# ---------------------------------------------------------------------------


@dataclass
class KvnBlock:
    """
    One logical block of KVN lines.

    For segment-based types (OEM, AEM, TDM) a block corresponds to one
    ``META_START…META_STOP`` + following data lines, or to one
    ``COVARIANCE_START…COVARIANCE_STOP`` section.  For flat types (OMM, OPM,
    APM, RDM, CDM) a single block holds all lines after the header.

    Attributes
    ----------
    meta : list[KvnLine]
        Lines inside ``META_START…META_STOP``.
    data : list[KvnLine]
        Lines inside ``DATA_START…DATA_STOP``, raw packed-data lines that
        follow ``META_STOP`` (OEM), or all non-header lines for flat types.
    covariance : list[KvnLine]
        Lines inside ``COVARIANCE_START…COVARIANCE_STOP``.
        Only populated when this block represents a covariance section.
    """

    meta: list[KvnLine] = field(default_factory=list)
    data: list[KvnLine] = field(default_factory=list)
    covariance: list[KvnLine] = field(default_factory=list)


@dataclass
class KvnDocument:
    """
    The fully split representation of a KVN file.

    Attributes
    ----------
    ndm_type : object
        The :class:`~ccsds_ndm.mapping._NdmDataType` enum member identifying
        the message type and associated xsdata class.
    header : list[KvnLine]
        Lines before the first section marker (includes the ``CCSDS_*_VERS``
        line and any top-level ``COMMENT`` / ``CREATION_DATE`` / ``ORIGINATOR``
        lines).
    segments : list[KvnBlock]
        Ordered list of blocks.  For segment-based types each entry is a
        META+data block or a standalone covariance block.  For flat types
        there is exactly one entry containing all data lines.
    """

    ndm_type: object
    header: list[KvnLine] = field(default_factory=list)
    segments: list[KvnBlock] = field(default_factory=list)


# ---------------------------------------------------------------------------
# State-machine constants
# ---------------------------------------------------------------------------

_HEADER = "HEADER"
_IN_META = "IN_META"
_AFTER_META = "AFTER_META"
_IN_DATA = "IN_DATA"
_IN_COVARIANCE = "IN_COVARIANCE"


# ---------------------------------------------------------------------------
# Block parser
# ---------------------------------------------------------------------------


def parse_blocks(lines: list[KvnLine]) -> KvnDocument:
    """
    Split a tokenised KVN line list into a :class:`KvnDocument`.

    Identifies the NDM message type from the ``CCSDS_*_VERS`` header line,
    then drives a state machine over the lines to produce an ordered list of
    :class:`KvnBlock` objects.  See the module docstring for the full
    description of state transitions and the flat-type fallback.

    Parameters
    ----------
    lines : list[KvnLine]
        Output of :func:`~ccsds_ndm.kvn_utils_tokenizer.tokenize`.

    Returns
    -------
    KvnDocument
        Fully split document with NDM type resolved and lines grouped into
        header + ordered :class:`KvnBlock` segments.

    Raises
    ------
    ValueError
        If no ``CCSDS_*_VERS`` header line is found in *lines*.
    """
    from ccsds_ndm.mapping import _NdmDataType

    # --- Step A: identify NDM type ---
    ndm_type = None
    for line in lines:
        if isinstance(line, KvLine) and line.key.startswith("CCSDS_"):
            ndm_type = _NdmDataType.find_ndm_type_by_class_id(line.key, line.value)
            break
    if ndm_type is None:
        raise ValueError("No CCSDS_*_VERS header line found in KVN data.")

    # --- Step B: state machine ---
    state = _HEADER
    header: list[KvnLine] = []
    segments: list[KvnBlock] = []
    current_block: KvnBlock | None = None

    for line in lines:
        if isinstance(line, SectionMarkerLine):
            # Flush open AFTER_META block before starting a new section
            if state == _AFTER_META and current_block is not None:
                if line.key in ("META_START", "COVARIANCE_START"):
                    segments.append(current_block)
                    current_block = None

            match line.key:
                case "META_START":
                    current_block = KvnBlock()
                    state = _IN_META
                case "META_STOP":
                    state = _AFTER_META
                case "DATA_START":
                    state = _IN_DATA
                case "DATA_STOP":
                    assert current_block is not None
                    segments.append(current_block)
                    current_block = None
                    state = _HEADER
                case "COVARIANCE_START":
                    current_block = KvnBlock()
                    state = _IN_COVARIANCE
                case "COVARIANCE_STOP":
                    assert current_block is not None
                    segments.append(current_block)
                    current_block = None
                    state = _HEADER
            continue  # section markers are not stored in any list

        if state == _HEADER:
            header.append(line)
        elif state == _IN_META:
            assert current_block is not None
            current_block.meta.append(line)
        elif state == _AFTER_META:
            assert current_block is not None
            current_block.data.append(line)
        elif state == _IN_DATA:
            assert current_block is not None
            current_block.data.append(line)
        elif state == _IN_COVARIANCE:
            assert current_block is not None
            current_block.covariance.append(line)

    # Flush any remaining AFTER_META block (last OEM segment with no trailing marker)
    if state == _AFTER_META and current_block is not None:
        segments.append(current_block)

    # --- Step C: flat-type fallback ---
    if not segments:
        block = KvnBlock(data=header[1:])
        segments.append(block)
        header = header[:1]

    return KvnDocument(ndm_type=ndm_type, header=header, segments=segments)
