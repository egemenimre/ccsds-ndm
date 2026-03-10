# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Handler category sentinels and TypeHandler namedtuple for the KVN registry.

Each xsdata type is identified by its class name (str) and mapped to a
``TypeHandler`` namedtuple that classifies its locator, parser, and writer.
Types absent from a schema registry implicitly use ``DEFAULT_HANDLER``.

There is one registry dict per NDM schema version (e.g. ``ndmxml2.REGISTRY``
for ndmxml 2.0).  The string class name can be resolved to the actual class
at runtime via the schema's ``__init__.py`` imports.

Handler categories
------------------
Locators (``locate``)
~~~~~~~~~~~~~~~~~~~~~
Classify a span of KvnLines as belonging to one instance of a type.

``LOC_DEFAULT``
    Keyword-set matching via ``get_ccsds_kw_list``.  A new instance starts
    when a keyword belonging to this type's keyword set appears, and ends at
    the first repetition of that keyword or at a block boundary.
    Works for every flat KEY = VALUE container (NdmHeader, OpmMetadata,
    StateVectorType, ManeuverParametersType, SpacecraftParametersType, …).

``LOC_PACKED_STATE``
    Epoch-led packed lines (``EPOCH X Y Z X_DOT Y_DOT Z_DOT [X_DDOT …]``).
    Each logical record is one text line; a new instance starts on the next
    non-comment line.  Used by ``StateVectorAccType`` (OEM data rows).

``LOC_PACKED_ATTITUDE``
    Epoch-led packed lines whose column count and semantics depend on
    ``ATTITUDE_TYPE`` from the enclosing segment's metadata.
    Used by ``AttitudeStateType`` (AEM data rows).

``LOC_COVARIANCE``
    Starts on an ``EPOCH`` keyword line, followed by an optional
    ``COV_REF_FRAME`` keyword line, then 6 lower-triangular numeric rows
    (21 values total).  Used by ``OemCovarianceMatrixType``.

``LOC_TDM_OBS``
    Each observation is ``KEY = EPOCH VALUE`` on one line inside
    DATA_START / DATA_STOP markers.
    Used by ``TrackingDataObservationType``.

``LOC_PACKED_LINES``
    Mixed block: KEY=VALUE header fields followed by a packed ``list[str]``
    (``trajLine`` / ``attLine`` / ``covLine``).  One instance starts when the
    anchor keyword (first declared uppercase field) appears; ends before the
    next occurrence of that same anchor.
    Used by ``OcmTrajStateType``, ``OcmCovarianceMatrixType``,
    ``AcmAttitudeStateType``, ``AcmCovarianceMatrixType``.

Parsers (``parse``)
~~~~~~~~~~~~~~~~~~~
Convert located KvnLines into an xsdata object.

``PARSE_DEFAULT``
    Splits each line into ``[keyword, value, unit]`` and feeds the result
    to ``build_ndm_object`` from ``kvn_utils``.  Sub-containers are handled
    by recursing through the registry.  Works for all KEY = VALUE types.

``PARSE_PACKED_STATE``
    Splits one packed line on whitespace → positional columns for EPOCH, X,
    Y, Z, X_DOT, Y_DOT, Z_DOT (+ optional X_DDOT, Y_DDOT, Z_DDOT) →
    ``StateVectorAccType``.

``PARSE_PACKED_ATTITUDE``
    Splits one packed line on whitespace; derives the column template from
    ``ctx['meta'].attitude_type`` (and ``euler_rot_seq`` where needed), then
    populates the appropriate sub-object inside ``AttitudeStateType``:
    one of quaternion_state, quaternion_derivative, quaternion_euler_rate,
    euler_angle, euler_angle_rate, spin, spin_nutation.

``PARSE_COVARIANCE``
    Reads the EPOCH (and optional COV_REF_FRAME) keyword lines, then the
    6 lower-triangular numeric rows → ``OemCovarianceMatrixType``.

``PARSE_TDM_OBS``
    Splits the ``KEY = EPOCH VALUE`` line into keyword, epoch, value →
    ``TrackingDataObservationType``.

``PARSE_ROTATION_ANGLE``
    The keyword is NOT fixed — it comes from the ``angle`` discriminator
    attribute (X_ANGLE / Y_ANGLE / Z_ANGLE).  Reads up to 3 such lines →
    ``RotationAngleType``.

``PARSE_ROTATION_RATE``
    Analogous to ``PARSE_ROTATION_ANGLE`` for the ``rate`` discriminator
    (X_RATE / Y_RATE / Z_RATE) → ``RotationRateType``.

``PARSE_PACKED_LINES``
    Reads KEY=VALUE header fields via the default parser, then stores each
    remaining packed text line verbatim into the embedded ``list[str]`` field.
    Used by ``OcmTrajStateType``, ``OcmCovarianceMatrixType``,
    ``AcmAttitudeStateType``, ``AcmCovarianceMatrixType``.

Writers (``write``)
~~~~~~~~~~~~~~~~~~~
Serialise an xsdata object to a list of KvnLines.

``WRITE_DEFAULT``
    Iterates dataclass fields in declaration order:

    - ``str`` / ``int`` / ``float`` / ``Enum`` leaf → one ``KvnLine``
      (keyword from field metadata ``"name"``, value, unit from the ``units``
      attribute on the value object if present).
    - ``list[str]`` (COMMENT) → one ``CommentLine`` per entry.
    - sub-container → recurse via registry.

    Works for all KEY = VALUE containers.

``WRITE_PACKED_STATE``
    Emits one line per ``StateVectorAccType``:
    ``EPOCH X Y Z X_DOT Y_DOT Z_DOT [X_DDOT Y_DDOT Z_DDOT]``.

``WRITE_PACKED_ATTITUDE``
    Emits one line per ``AttitudeStateType``; column order derived from the
    populated sub-object and ``ctx['meta'].attitude_type``.

``WRITE_COVARIANCE``
    Emits ``EPOCH`` (and optional ``COV_REF_FRAME``) keyword lines then the
    6 lower-triangular numeric rows.

``WRITE_TDM_OBS``
    Emits ``KEY = EPOCH VALUE`` for each ``TrackingDataObservationType``.

``WRITE_ROTATION_ANGLE``
    Emits up to 3 lines, keyword from ``rotation.angle``
    (X_ANGLE / Y_ANGLE / Z_ANGLE) → ``RotationAngleType``.

``WRITE_ROTATION_RATE``
    Analogous to ``WRITE_ROTATION_ANGLE`` for the ``rate`` discriminator
    (X_RATE / Y_RATE / Z_RATE) → ``RotationRateType``.

``WRITE_PACKED_LINES``
    Emits the KEY=VALUE header fields first, then one text line per entry in
    the embedded packed ``list[str]`` field (``trajLine`` / ``attLine`` /
    ``covLine``).  Used by ``OcmTrajStateType``, ``OcmCovarianceMatrixType``,
    ``AcmAttitudeStateType``, and ``AcmCovarianceMatrixType``.

Document-level dispatch (structural, not per-type)
--------------------------------------------------
``DISPATCH_FLAT``
    OPM, OMM, APM, RDM — single segment, no META_START/STOP markers.
    Partition lines into header / metadata / data buckets by keyword-set
    membership, then call the registry for each bucket.

``DISPATCH_SEGMENTED``
    OEM, AEM, TDM — one or more segments delimited by
    META_START / META_STOP / DATA_START / DATA_STOP
    (plus COVARIANCE_START / COVARIANCE_STOP for OEM).
    A state machine yields ``(meta_lines, data_lines[, cov_lines])`` per
    segment before calling the registry.

``DISPATCH_CDM``
    CDM — split on OBJECT_1 / OBJECT_2 keywords; handle the
    RELATIVE_METADATA_DATA section separately.
"""

from __future__ import annotations

from typing import NamedTuple, Protocol

# ---------------------------------------------------------------------------
# Handler category sentinels
# ---------------------------------------------------------------------------

# -- Locators
LOC_DEFAULT = "LOC_DEFAULT"
LOC_PACKED_STATE = "LOC_PACKED_STATE"
LOC_PACKED_ATTITUDE = "LOC_PACKED_ATTITUDE"
LOC_COVARIANCE = "LOC_COVARIANCE"
LOC_TDM_OBS = "LOC_TDM_OBS"
LOC_PACKED_LINES = "LOC_PACKED_LINES"

# -- Parsers
PARSE_DEFAULT = "PARSE_DEFAULT"
PARSE_PACKED_STATE = "PARSE_PACKED_STATE"
PARSE_PACKED_ATTITUDE = "PARSE_PACKED_ATTITUDE"
PARSE_COVARIANCE = "PARSE_COVARIANCE"
PARSE_TDM_OBS = "PARSE_TDM_OBS"
PARSE_ROTATION_ANGLE = "PARSE_ROTATION_ANGLE"
PARSE_ROTATION_RATE = "PARSE_ROTATION_RATE"
PARSE_PACKED_LINES = "PARSE_PACKED_LINES"

# -- Writers
WRITE_DEFAULT = "WRITE_DEFAULT"
WRITE_PACKED_STATE = "WRITE_PACKED_STATE"
WRITE_PACKED_ATTITUDE = "WRITE_PACKED_ATTITUDE"
WRITE_COVARIANCE = "WRITE_COVARIANCE"
WRITE_TDM_OBS = "WRITE_TDM_OBS"
WRITE_ROTATION_ANGLE = "WRITE_ROTATION_ANGLE"
WRITE_ROTATION_RATE = "WRITE_ROTATION_RATE"
WRITE_PACKED_LINES = "WRITE_PACKED_LINES"

# -- Document-level dispatch
DISPATCH_FLAT = "DISPATCH_FLAT"
DISPATCH_SEGMENTED = "DISPATCH_SEGMENTED"
DISPATCH_CDM = "DISPATCH_CDM"


# ---------------------------------------------------------------------------
# TypeHandler namedtuple
# ---------------------------------------------------------------------------


class TypeHandler(NamedTuple):
    """
    Handler classification for one xsdata type.

    Each field holds a sentinel string from the constants above.
    All three slots must be explicitly filled.
    Types not present in a schema registry implicitly use ``DEFAULT_HANDLER``.

    Fields
    ------
    locate:
        Which locator strategy to use.
    parse:
        Which parser strategy to use.
    write:
        Which writer strategy to use.
    """

    locate: str
    parse: str
    write: str


# Convenience alias for the all-default case (also the implicit fallback)
DEFAULT_HANDLER = TypeHandler(LOC_DEFAULT, PARSE_DEFAULT, WRITE_DEFAULT)


class SchemaRegistry(Protocol):
    """Structural type for schema-specific KVN registries (ndmxml1, ndmxml2, …)."""

    version: int
    segmented_ids: frozenset[str]
    cdm_ids: frozenset[str]
    registry: dict[str, TypeHandler]
    dispatch: dict[str, str]

    def get_handler(self, cls_name: str) -> TypeHandler: ...  # noqa: E704
