# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
KVN parser: type identification, document dispatch, and block location.

Phase 1 implements:
  1. ``identify_ndm_type``   — scan tokenised lines for ``CCSDS_*_VERS``
  2. ``dispatch_document``   — split lines into header + Segment list
                               (flat / segmented / CDM structural variants)
  3. ``locate_blocks``       — given a list of KvLine objects and a target
                               dataclass, return the keyword-boundary spans
                               for every instance of that class (DEFAULT
                               locator only — no packed/covariance yet)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum

from ccsds_ndm.kvn_registry import VERSION_REGISTRY as _VERSION_REGISTRY
from ccsds_ndm.kvn_tokenizer import (
    BlankLine,
    CommentLine,
    KvLine,
    KvnLine,
    PackedDataLine,
    SectionMarkerLine,
    TdmObsLine,
)
from ccsds_ndm.mapping import _NdmDataType

# ---------------------------------------------------------------------------
# Data structures produced by the dispatcher
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    """
    One logical NDM segment as extracted by the document dispatcher.

    For segmented types (OEM, AEM, TDM) each ``META_START/STOP`` block
    produces one ``Segment``; a ``COVARIANCE_START/STOP`` block also produces
    a ``Segment`` with only ``covariance`` populated.

    For flat types (OPM, OMM, APM, RDM, CDM) there is exactly one ``Segment``
    with all non-header lines in ``data``.
    """

    meta: list[KvnLine] = field(default_factory=list)
    data: list[KvnLine] = field(default_factory=list)
    covariance: list[KvnLine] = field(default_factory=list)


@dataclass
class KvnDocument:
    """
    Top-level representation of a dispatched KVN file.

    Attributes
    ----------
    ndm_type : _NdmDataType
        Enum member identifying the message type and xsdata class.
    header : list[KvnLine]
        Lines that belong to the NDM header (``CCSDS_*_VERS``,
        ``CREATION_DATE``, ``ORIGINATOR``, and top-level ``COMMENT`` lines).
    segments : list[Segment]
        Ordered list of logical segments.  One entry for flat types; one per
        ``META_START/STOP`` block (plus optional covariance segments) for
        segmented types.
    """

    ndm_type: _NdmDataType
    header: list[KvnLine] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 1 — Identify NDM type
# ---------------------------------------------------------------------------


def identify_ndm_type(lines: list[KvnLine]) -> _NdmDataType:
    """
    Scan tokenised KVN lines and return the matching :class:`_NdmDataType`.

    Searches for the first ``KvLine`` whose key starts with ``"CCSDS_"`` and
    delegates to :meth:`_NdmDataType.find_ndm_type_by_class_id`.

    Parameters
    ----------
    lines : list[KvnLine]
        Output of :func:`~ccsds_ndm.kvn_utils.kvn_utils_tokenizer.tokenize`.

    Returns
    -------
    _NdmDataType

    Raises
    ------
    ValueError
        If no ``CCSDS_*_VERS`` line is found.
    """
    for line in lines:
        if isinstance(line, KvLine) and line.key.startswith("CCSDS_"):
            return _NdmDataType.find_ndm_type_by_class_id(line.key, line.value.strip())
    raise ValueError("No CCSDS_*_VERS header line found in KVN data.")


# ---------------------------------------------------------------------------
# Step 2 — Document-level dispatch
# ---------------------------------------------------------------------------


class ParserState(Enum):
    """State machine states for document-level dispatch."""

    HEADER = "HEADER"
    IN_META = "IN_META"
    AFTER_META = "AFTER_META"
    IN_DATA = "IN_DATA"
    IN_COVARIANCE = "IN_COVARIANCE"


class CdmBucket(IntEnum):
    """Bucket indices for CDM document structure."""

    HEADER = 0
    REL_META = 1
    OBJECT_1 = 2
    OBJECT_2 = 3


def dispatch_document(lines: list[KvnLine]) -> KvnDocument:
    """
    Split a tokenised KVN line list into a :class:`KvnDocument`.

    Identifies the NDM type from the ``CCSDS_*_VERS`` header line and then
    routes to one of three structural variants:

    * **Segmented** (OEM, AEM, TDM) — state machine over
      ``META_START/STOP``, ``DATA_START/STOP``,
      ``COVARIANCE_START/STOP`` markers.
    * **Flat** (OPM, OMM, APM, RDM) — no markers; all lines after the first
      ``CCSDS_*_VERS`` line form one segment (meta lines are separated from
      data lines by the locator later).
    * **CDM** — split on ``OBJECT_1`` / ``OBJECT_2`` keyword occurrences;
      ``RELATIVE_METADATA_DATA`` section handled as separate segment.

    Parameters
    ----------
    lines : list[KvnLine]
        Output of :func:`tokenize`.

    Returns
    -------
    KvnDocument
    """
    ndm_type = identify_ndm_type(lines)
    ndm_id = ndm_type.ndm_id  # lowercase, e.g. "oem", "opm"
    reg = _VERSION_REGISTRY[ndm_type.req_combi_version]

    if ndm_id in reg.segmented_ids:
        header, segments = _dispatch_segmented(lines)
    elif ndm_id in reg.cdm_ids:
        header, segments = _dispatch_cdm(lines)
    else:
        header, segments = _dispatch_flat(lines)

    return KvnDocument(ndm_type=ndm_type, header=header, segments=segments)


# -- Segmented dispatch (OEM, AEM, TDM) -------------------------------------


def _dispatch_segmented(lines: list[KvnLine]) -> tuple[list[KvnLine], list[Segment]]:
    """State-machine dispatch for segment-based message types."""
    state = ParserState.HEADER
    header: list[KvnLine] = []
    segments: list[Segment] = []
    current: Segment | None = None

    for line in lines:
        if isinstance(line, SectionMarkerLine):
            # Flush an open AFTER_META segment when a new section begins
            if state == ParserState.AFTER_META and current is not None:
                if line.key in ("META_START", "COVARIANCE_START"):
                    segments.append(current)
                    current = None

            match line.key:
                case "META_START":
                    current = Segment()
                    state = ParserState.IN_META
                case "META_STOP":
                    state = ParserState.AFTER_META
                case "DATA_START":
                    # TDM: data block follows DATA_START without packed lines
                    if current is None:
                        current = Segment()
                    state = ParserState.IN_DATA
                case "DATA_STOP":
                    if current is not None:
                        segments.append(current)
                        current = None
                    state = ParserState.HEADER
                case "COVARIANCE_START":
                    current = Segment()
                    state = ParserState.IN_COVARIANCE
                case "COVARIANCE_STOP":
                    if current is not None:
                        segments.append(current)
                        current = None
                    state = ParserState.HEADER
            continue  # section markers are not stored in any list

        if isinstance(line, BlankLine):
            if state == ParserState.HEADER:
                header.append(line)
            elif state in (
                ParserState.IN_META,
                ParserState.AFTER_META,
                ParserState.IN_DATA,
            ):
                if current is not None:
                    current.data.append(line)
            continue

        if state == ParserState.HEADER:
            header.append(line)
        elif state == ParserState.IN_META:
            if current is None:
                raise ValueError("Parser state IN_META but no current segment exists.")
            current.meta.append(line)
        elif state == ParserState.AFTER_META:
            # OEM: packed data lines follow META_STOP without DATA_START
            if current is None:
                raise ValueError("Parser state AFTER_META but no current segment exists.")
            current.data.append(line)
        elif state == ParserState.IN_DATA:
            if current is None:
                raise ValueError("Parser state IN_DATA but no current segment exists.")
            current.data.append(line)
        elif state == ParserState.IN_COVARIANCE:
            if current is None:
                raise ValueError("Parser state IN_COVARIANCE but no current segment exists.")
            current.covariance.append(line)

    # Flush any remaining AFTER_META segment (last OEM segment)
    if state == ParserState.AFTER_META and current is not None:
        segments.append(current)

    return header, segments


# -- Flat dispatch (OPM, OMM, APM, RDM) ------------------------------------

# Keywords that belong to the header (flat types have no META_START/STOP)
_HEADER_KWS = frozenset(
    {
        "CREATION_DATE",
        "ORIGINATOR",
        "MESSAGE_ID",
        "MESSAGE_FOR",
    }
)


def _dispatch_flat(lines: list[KvnLine]) -> tuple[list[KvnLine], list[Segment]]:
    """
    Dispatch for flat message types (OPM, OMM, APM, RDM).

    The first ``KvLine`` is the ``CCSDS_*_VERS`` line (goes to header only).
    Subsequent header keyword lines (``CREATION_DATE``, ``ORIGINATOR``,
    ``MESSAGE_ID``) also go to the header.  All remaining lines form a single
    ``Segment.data`` list; the locator will further partition them into
    metadata / data sub-blocks.
    """
    header: list[KvnLine] = []
    body: list[KvnLine] = []

    vers_seen = False
    in_header_section = False

    for line in lines:
        if isinstance(line, BlankLine):
            if not vers_seen:
                continue
            if in_header_section:
                header.append(line)
            else:
                body.append(line)
            continue

        if isinstance(line, KvLine) and line.key.startswith("CCSDS_") and not vers_seen:
            header.append(line)
            vers_seen = True
            in_header_section = True
            continue

        if in_header_section and isinstance(line, KvLine) and line.key in _HEADER_KWS:
            header.append(line)
            continue

        # First non-header-kw line: switch to body permanently
        in_header_section = False
        body.append(line)

    seg = Segment(data=body)
    return header, [seg]


# -- CDM dispatch -----------------------------------------------------------


def _dispatch_cdm(lines: list[KvnLine]) -> tuple[list[KvnLine], list[Segment]]:
    """
    Dispatch for CDM files.

    CDM structure:
    - Header section (CCSDS_CDM_VERS, CREATION_DATE, ORIGINATOR, MESSAGE_*)
    - Relative metadata section (TCA, MISS_DISTANCE, … up to first OBJECT line)
    - Object 1 section (OBJECT = OBJECT1 … up to next OBJECT line)
    - Object 2 section (OBJECT = OBJECT2 … to end)

    The two object sections are delimited by ``OBJECT`` keyword lines whose
    value is ``OBJECT1`` or ``OBJECT2`` (not separate OBJECT_1/OBJECT_2 keys).

    We produce:
    - ``header``       — top-level header lines
    - ``segments[0]``  — relative metadata lines (Segment.meta)
    - ``segments[1]``  — OBJECT 1 lines (Segment.data)
    - ``segments[2]``  — OBJECT 2 lines (Segment.data)
    """
    header: list[KvnLine] = []
    rel_meta: list[KvnLine] = []
    obj1: list[KvnLine] = []
    obj2: list[KvnLine] = []

    bucket = CdmBucket.HEADER
    vers_seen = False
    pending_comments: list[KvnLine] = []  # comments buffered until bucket is determined

    for line in lines:
        if isinstance(line, BlankLine):
            if not vers_seen:
                continue
            # If comments are pending, buffer the blank with them so the blank
            # stays between the comments (preserving the inter-comment gap).
            if pending_comments:
                pending_comments.append(line)
            else:
                [header, rel_meta, obj1, obj2][bucket].append(line)
            continue

        # Buffer comments: we don't know which bucket they belong to until the
        # next KvLine triggers a potential bucket transition (e.g. "Relative
        # Metadata/Data" appears before TCA which flips HEADER→REL_META).
        if isinstance(line, CommentLine):
            pending_comments.append(line)
            continue

        if isinstance(line, KvLine):
            if line.key.startswith("CCSDS_") and not vers_seen:
                header.append(line)
                vers_seen = True
                pending_comments.clear()
                continue

            # Switch to rel_meta after the known header keywords are exhausted
            if bucket == CdmBucket.HEADER and line.key not in _HEADER_KWS:
                bucket = CdmBucket.REL_META

            # OBJECT = OBJECT1 / OBJECT2 delimit the two object sections
            if line.key == "OBJECT":
                if line.value.strip() == "OBJECT1":
                    bucket = CdmBucket.OBJECT_1
                elif line.value.strip() == "OBJECT2":
                    bucket = CdmBucket.OBJECT_2

        # Flush buffered comments into the now-resolved bucket, then add line
        buckets = [header, rel_meta, obj1, obj2]
        buckets[bucket].extend(pending_comments)
        pending_comments.clear()
        buckets[bucket].append(line)

    segments = [
        Segment(meta=rel_meta),
        Segment(data=obj1),
        Segment(data=obj2),
    ]
    return header, segments


# ---------------------------------------------------------------------------
# Step 3 — Default locator
# ---------------------------------------------------------------------------


@dataclass
class BlockSpan:
    """
    A located sub-block within a list of KvnLines.

    Attributes
    ----------
    start : int
        Index of the first line (inclusive) in the source list.
    end : int
        Index one past the last line (exclusive) in the source list.
    lines : list[KvnLine]
        The actual lines within [start, end).
    """

    start: int
    end: int
    lines: list[KvnLine]


def locate_blocks(
    lines: list[KvnLine],
    cls,
) -> list[BlockSpan]:
    """
    Locate every instance of ``cls`` within ``lines`` using the default
    keyword-set strategy (``LOC_DEFAULT``).

    The keyword set for ``cls`` is derived from its dataclass field metadata
    (``"name"`` entries that are ALL_UPPER strings).  A new instance of
    ``cls`` is considered to start whenever the anchor keyword (first declared
    uppercase field) is encountered, and to end just before the next
    occurrence of that same anchor keyword (or at end-of-list).

    This covers every flat ``KEY = VALUE`` container: ``NdmHeader``,
    ``OpmMetadata``, ``StateVectorType``, ``ManeuverParametersType``,
    ``SpacecraftParametersType``, ``KeplerianElementsType``, etc.

    Packed-data, covariance, and TDM-observation types are NOT handled here;
    they will be covered by their own locators in later phases.

    Parameters
    ----------
    lines : list[KvnLine]
        Source lines for one segment bucket (e.g. ``Segment.data`` for flat
        types, or ``Segment.meta`` for metadata-only classes).
    cls : type
        The dataclass whose instances are to be located.

    Returns
    -------
    list[BlockSpan]
        Ordered list of located spans, one per detected instance.
    """
    # Collect every keyword name declared by cls (e.g. {"EPOCH", "X", "Y", …}).
    # Non-uppercase field names (nested objects, metadata) are excluded.
    kw_set = _kw_set_for(cls)
    if not kw_set:
        # cls has no uppercase KVN fields — nothing to locate
        return []

    # The anchor is the first uppercase field; it delimits individual instances.
    # Example: for StateVectorType the anchor is "EPOCH".
    anchor = _anchor_kw_for(cls)
    if anchor is None:
        # No single field can serve as an instance delimiter (rare).
        # Treat the entire line list as one span if it contains any member kw.
        member_positions = [
            i
            for i, ln in enumerate(lines)
            if isinstance(ln, KvLine) and ln.key in kw_set
        ]
        if not member_positions:
            return []
        # Span from the first matching kw to the last (inclusive)
        return [
            BlockSpan(
                start=member_positions[0],
                end=member_positions[-1] + 1,
                lines=lines[member_positions[0] : member_positions[-1] + 1],
            )
        ]

    # Find every line index where the anchor keyword appears.
    # Each occurrence marks the start of a new instance of cls.
    anchor_positions = [
        i for i, ln in enumerate(lines) if isinstance(ln, KvLine) and ln.key == anchor
    ]

    if not anchor_positions:
        # Anchor is optional in this message (e.g. EPOCH absent in some blocks).
        # Fall back: form one span from the first to last member keyword.
        member_positions = [
            i
            for i, ln in enumerate(lines)
            if isinstance(ln, KvLine) and ln.key in kw_set
        ]
        if not member_positions:
            return []
        return [
            BlockSpan(
                start=member_positions[0],
                end=member_positions[-1] + 1,
                lines=lines[member_positions[0] : member_positions[-1] + 1],
            )
        ]

    spans: list[BlockSpan] = []
    for idx, pos in enumerate(anchor_positions):
        # The raw chunk runs from this anchor up to (but not including) the
        # next anchor — or to the end of the list for the last instance.
        next_pos = (
            anchor_positions[idx + 1] if idx + 1 < len(anchor_positions) else len(lines)
        )
        chunk = lines[pos:next_pos]

        # Clip: find the last line in the chunk whose key belongs to kw_set.
        # This stops the span from absorbing lines that belong to the next
        # sibling block (e.g. StateVectorType should not grab keplerian keys).
        last_kw_offset = -1
        for i, ln in enumerate(chunk):
            if isinstance(ln, KvLine) and ln.key in kw_set:
                last_kw_offset = i

        if last_kw_offset == -1:
            continue  # anchor present but no member keywords — skip empty chunk

        # Trim the chunk to end at the last recognised keyword
        chunk = chunk[: last_kw_offset + 1]
        spans.append(BlockSpan(start=pos, end=pos + last_kw_offset + 1, lines=chunk))

    return spans


# ---------------------------------------------------------------------------
# Step 3b — Packed-state locator (OEM state vectors)
# ---------------------------------------------------------------------------


def locate_packed_state(lines: list[KvnLine]) -> list[BlockSpan]:
    """
    Locate every ``PackedDataLine`` in *lines* as one ``BlockSpan`` each.

    Each packed line represents a single epoch-led state vector record
    (``EPOCH X Y Z X_DOT Y_DOT Z_DOT [X_DDOT …]``).  Used by
    ``StateVectorAccType`` in OEM data sections.

    Parameters
    ----------
    lines : list[KvnLine]
        Typically ``Segment.data`` from an OEM segment.

    Returns
    -------
    list[BlockSpan]
    """
    return [
        BlockSpan(start=i, end=i + 1, lines=[ln])
        for i, ln in enumerate(lines)
        if isinstance(ln, PackedDataLine)
    ]


# ---------------------------------------------------------------------------
# Step 3c — Packed-attitude locator (AEM attitude states)
# ---------------------------------------------------------------------------


def locate_packed_attitude(lines: list[KvnLine]) -> list[BlockSpan]:
    """
    Locate every ``PackedDataLine`` in *lines* as one ``BlockSpan`` each.

    Identical to :func:`locate_packed_state` in structure — each packed line
    is one attitude state record.  Column interpretation (quaternion, Euler,
    spin, …) is determined later by the parser using segment metadata.
    Used by ``AttitudeStateType`` in AEM data sections.

    Parameters
    ----------
    lines : list[KvnLine]
        Typically ``Segment.data`` from an AEM segment.

    Returns
    -------
    list[BlockSpan]
    """
    return [
        BlockSpan(start=i, end=i + 1, lines=[ln])
        for i, ln in enumerate(lines)
        if isinstance(ln, PackedDataLine)
    ]


# ---------------------------------------------------------------------------
# Step 3d — Covariance locator (OEM covariance matrices)
# ---------------------------------------------------------------------------


def locate_covariance(lines: list[KvnLine]) -> list[BlockSpan]:
    """
    Locate every covariance matrix instance in *lines*.

    A covariance instance starts at an ``EPOCH`` keyword line and spans
    until the next ``EPOCH`` line or end-of-list.  Each instance typically
    contains the ``EPOCH`` line, an optional ``COV_REF_FRAME`` line, and
    6 ``CovarianceRowLine`` objects (21 lower-triangular values total).
    Used by ``OemCovarianceMatrixType``.

    Parameters
    ----------
    lines : list[KvnLine]
        Typically ``Segment.covariance`` from an OEM segment.

    Returns
    -------
    list[BlockSpan]
    """
    # Find all EPOCH positions — each starts a new covariance instance
    epoch_positions = [
        i for i, ln in enumerate(lines) if isinstance(ln, KvLine) and ln.key == "EPOCH"
    ]

    if not epoch_positions:
        return []

    spans: list[BlockSpan] = []
    for idx, pos in enumerate(epoch_positions):
        next_pos = (
            epoch_positions[idx + 1] if idx + 1 < len(epoch_positions) else len(lines)
        )
        chunk = lines[pos:next_pos]
        spans.append(BlockSpan(start=pos, end=next_pos, lines=chunk))

    return spans


# ---------------------------------------------------------------------------
# Step 3e — TDM observation locator
# ---------------------------------------------------------------------------


def locate_tdm_obs(lines: list[KvnLine]) -> list[BlockSpan]:
    """
    Locate every ``TdmObsLine`` in *lines* as one ``BlockSpan`` each.

    Each TDM observation is a single ``KEY = EPOCH VALUE`` line.
    Used by ``TrackingDataObservationType`` in TDM data sections.

    Parameters
    ----------
    lines : list[KvnLine]
        Typically ``Segment.data`` from a TDM segment.

    Returns
    -------
    list[BlockSpan]
    """
    return [
        BlockSpan(start=i, end=i + 1, lines=[ln])
        for i, ln in enumerate(lines)
        if isinstance(ln, TdmObsLine)
    ]


# ---------------------------------------------------------------------------
# Step 3f — Packed-lines locator (OCM/ACM mixed blocks)
# ---------------------------------------------------------------------------


def locate_packed_lines(
    lines: list[KvnLine],
    cls,
) -> list[BlockSpan]:
    """
    Locate every instance of ``cls`` in *lines* using the anchor-keyword
    strategy, including non-KvLine rows within each span.

    Like :func:`locate_blocks` but does **not** clip spans at the last
    matching keyword — packed text lines (trajectory / attitude / covariance
    rows stored as plain strings) that follow the KEY=VALUE header are
    kept inside the span.  Used by ``OcmTrajStateType``,
    ``OcmCovarianceMatrixType``, ``AcmAttitudeStateType``, and
    ``AcmCovarianceMatrixType``.

    Parameters
    ----------
    lines : list[KvnLine]
        Source lines for one segment bucket.
    cls : type
        The dataclass whose instances are to be located.

    Returns
    -------
    list[BlockSpan]
    """
    anchor = _anchor_kw_for(cls)
    if anchor is None:
        return []

    # Find all anchor positions
    anchor_positions = [
        i for i, ln in enumerate(lines) if isinstance(ln, KvLine) and ln.key == anchor
    ]

    if not anchor_positions:
        return []

    spans: list[BlockSpan] = []
    for idx, pos in enumerate(anchor_positions):
        next_pos = (
            anchor_positions[idx + 1] if idx + 1 < len(anchor_positions) else len(lines)
        )
        chunk = lines[pos:next_pos]
        spans.append(BlockSpan(start=pos, end=next_pos, lines=chunk))

    return spans


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _kw_set_for(cls) -> frozenset[str]:
    """
    Return the set of all-uppercase KVN keyword names declared by ``cls``.

    Reads the ``"name"`` metadata from each dataclass field; keeps only
    entries that are fully uppercase (leaf KEY = VALUE fields).
    """
    if not hasattr(cls, "__dataclass_fields__"):
        return frozenset()
    return frozenset(
        f.metadata["name"]
        for f in cls.__dataclass_fields__.values()
        if "name" in f.metadata and f.metadata["name"].isupper()
    )


def _anchor_kw_for(cls) -> str | None:
    """
    Return the first all-uppercase KVN keyword declared by ``cls``.

    Field declaration order is preserved in ``__dataclass_fields__`` (Python
    3.7+), so the first uppercase-named field is a stable anchor.
    ``COMMENT`` is skipped because comment lines are ``CommentLine`` objects,
    not ``KvLine``s, and therefore cannot serve as instance delimiters.
    """
    if not hasattr(cls, "__dataclass_fields__"):
        return None
    for f in cls.__dataclass_fields__.values():
        name = f.metadata.get("name", "")
        if name.isupper() and name != "COMMENT":
            return name
    return None
