# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
KVN writer: serialise an xsdata dataclass tree to a list of
:class:`~ccsds_ndm.kvn_tokenizer.KvnLine` objects.

This is the inverse of :mod:`ccsds_ndm.kvn_builder`.  The public
entry point is :func:`write_kvn_lines`.

Uses the schema registry to dispatch document structure (flat /
segmented / CDM) and per-type special writers (packed state,
packed attitude, covariance, TDM observation, rotation types).
"""

from __future__ import annotations

import dataclasses
import typing
from decimal import Decimal
from enum import Enum

from ccsds_ndm.kvn_builder import _att_column_template, _hints, _unwrap
from ccsds_ndm.kvn_handlers import (
    DISPATCH_CDM,
    DISPATCH_SEGMENTED,
    WRITE_COVARIANCE,
    WRITE_PACKED_ATTITUDE,
    WRITE_PACKED_LINES,
    WRITE_PACKED_STATE,
    WRITE_ROTATION_ANGLE,
    WRITE_ROTATION_RATE,
    WRITE_TDM_OBS,
)
from ccsds_ndm.kvn_registry import VERSION_REGISTRY
from ccsds_ndm.kvn_tokenizer import (
    BlankLine,
    CommentLine,
    CovarianceRowLine,
    KvLine,
    KvnLine,
    PackedDataLine,
    SectionMarkerLine,
    TdmObsLine,
)
from ccsds_ndm.mapping import _NdmDataType

# ---------------------------------------------------------------------------
# Registry resolution
# ---------------------------------------------------------------------------


def _resolve_registry(ndm_obj):
    """Derive the :class:`SchemaRegistry` from the root NDM object."""
    ndm_type = _NdmDataType.find_ndm_type_by_class_id(ndm_obj.id, ndm_obj.version)
    return VERSION_REGISTRY[ndm_type.req_combi_version]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def write_kvn_lines(ndm_obj) -> list[KvnLine]:
    """
    Convert an xsdata NDM object tree to an ordered list of
    :class:`KvnLine` instances ready for rendering.

    Parameters
    ----------
    ndm_obj : object
        Root xsdata dataclass instance (e.g. ``Opm``, ``Oem``, …).

    Returns
    -------
    list[KvnLine]
        KVN lines.  Call ``line.to_str()`` on each and join with
        ``"\\n"`` to produce the final KVN text.
    """
    schema_reg = _resolve_registry(ndm_obj)

    # Version line
    lines: list[KvnLine] = [KvLine(key=ndm_obj.id, value=ndm_obj.version)]

    # Document dispatch
    root_cls_name = type(ndm_obj).__name__
    dispatch = schema_reg.dispatch.get(root_cls_name)

    if dispatch == DISPATCH_CDM:
        lines.extend(_write_cdm(ndm_obj, schema_reg))
    elif dispatch == DISPATCH_SEGMENTED:
        lines.extend(_write_segmented(ndm_obj, schema_reg))
    else:  # DISPATCH_FLAT
        lines.extend(_write_flat(ndm_obj, schema_reg))

    return lines


# ---------------------------------------------------------------------------
# Flat types (OPM, OMM, APM, RDM)
# ---------------------------------------------------------------------------


def _write_flat(ndm_obj, schema_reg) -> list[KvnLine]:
    lines: list[KvnLine] = []
    lines.append(BlankLine())
    lines.extend(_write_fields(ndm_obj.header, schema_reg))
    lines.append(BlankLine())
    seg = ndm_obj.body.segment
    lines.extend(_write_fields(seg.metadata, schema_reg))
    lines.append(BlankLine())
    lines.extend(_write_fields(seg.data, schema_reg, sep=True))
    return lines


# ---------------------------------------------------------------------------
# Segment-based types (OEM, AEM, TDM)
# ---------------------------------------------------------------------------

# Data class names that use DATA_START/DATA_STOP markers
_DATA_MARKER_TYPES = frozenset({"AemData", "TdmData"})


def _write_segmented(ndm_obj, schema_reg) -> list[KvnLine]:
    lines: list[KvnLine] = []
    lines.append(BlankLine())
    lines.extend(_write_fields(ndm_obj.header, schema_reg))
    lines.append(BlankLine())

    # Resolve data class for this type
    root_hints = _hints(type(ndm_obj))
    body_clazz = _unwrap(root_hints["body"])
    body_hints = _hints(body_clazz)
    seg_type_raw = body_hints["segment"]
    seg_clazz = _unwrap(seg_type_raw.__args__[0])
    seg_hints = _hints(seg_clazz)
    data_clazz = _unwrap(seg_hints["data"])
    data_cls_name = data_clazz.__name__

    for seg in ndm_obj.body.segment:
        # META block
        lines.append(SectionMarkerLine(key="META_START"))
        lines.extend(_write_fields(seg.metadata, schema_reg))
        lines.append(SectionMarkerLine(key="META_STOP"))
        lines.append(BlankLine())

        if data_cls_name in _DATA_MARKER_TYPES:
            lines.append(SectionMarkerLine(key="DATA_START"))

        # Data (covariance_matrix is written separately below for OEM)
        # DATA_MARKER_TYPES (TdmData, AemData) use packed/obs lines — no sep needed
        lines.extend(
            _write_fields(
                seg.data,
                schema_reg,
                sep=data_cls_name not in _DATA_MARKER_TYPES,
                seg_meta=seg.metadata,
                skip_fields=(
                    frozenset({"covariance_matrix"})
                    if data_cls_name == "OemData"
                    else frozenset()
                ),
            )
        )

        if data_cls_name in _DATA_MARKER_TYPES:
            lines.append(SectionMarkerLine(key="DATA_STOP"))

        # OEM covariance
        if (
            data_cls_name == "OemData"
            and hasattr(seg.data, "covariance_matrix")
            and seg.data.covariance_matrix
        ):
            lines.append(BlankLine())
            lines.append(SectionMarkerLine(key="COVARIANCE_START"))
            for cov in seg.data.covariance_matrix:
                lines.extend(_write_oem_covariance(cov))
            lines.append(SectionMarkerLine(key="COVARIANCE_STOP"))

        lines.append(BlankLine())

    return lines


# ---------------------------------------------------------------------------
# CDM (special flat with relative_metadata_data + object segments)
# ---------------------------------------------------------------------------


def _write_cdm(ndm_obj, schema_reg) -> list[KvnLine]:
    lines: list[KvnLine] = []
    body = ndm_obj.body

    # Header
    lines.append(BlankLine())
    lines.extend(_write_fields(ndm_obj.header, schema_reg))
    lines.append(BlankLine())

    # Relative metadata
    lines.extend(_write_fields(body.relative_metadata_data, schema_reg, sep=True))
    lines.append(BlankLine())

    # Object segments
    body_hints = _hints(type(body))
    seg_raw = body_hints["segment"]
    is_list_seg = getattr(seg_raw, "__origin__", None) is list
    segments = body.segment if is_list_seg else [body.segment]

    for seg in segments:
        lines.extend(_write_fields(seg.metadata, schema_reg))
        lines.append(BlankLine())
        lines.extend(_write_fields(seg.data, schema_reg, sep=True))
        lines.append(BlankLine())

    return lines


# ---------------------------------------------------------------------------
# Core recursive field writer
# ---------------------------------------------------------------------------


def _write_fields(
    obj,
    schema_reg,
    *,
    sep: bool = False,
    seg_meta=None,
    skip_fields: frozenset[str] = frozenset(),
) -> list[KvnLine]:
    """Recursively serialise an xsdata dataclass to KvnLines.

    Parameters
    ----------
    obj : object
        An xsdata dataclass instance.
    schema_reg : SchemaRegistry
        Schema registry for handler dispatch.
    sep : bool
        If *True*, insert :class:`BlankLine` separators before each
        camelCase sub-container field.
    seg_meta : object or None
        Segment metadata object, passed through for AEM template derivation.
    skip_fields : frozenset[str]
        Field names to skip entirely (e.g. fields handled separately by the
        caller, like ``covariance_matrix`` in OEM segments).
    """
    if obj is None:
        return []
    cls = type(obj)
    if not dataclasses.is_dataclass(cls):
        return []

    hints = _hints(cls)
    lines: list[KvnLine] = []

    for f in dataclasses.fields(cls):
        if f.name in skip_fields:
            continue
        value = getattr(obj, f.name)

        # Skip None optional fields
        if value is None:
            continue

        # Skip empty lists
        if isinstance(value, list) and not value:
            continue

        # Skip id and version (handled at top level)
        if f.name in ("id", "version"):
            continue

        # Skip Attribute-type fields (units, discriminators)
        if f.metadata.get("type") == "Attribute":
            continue

        meta_name = f.metadata.get("name")

        # COMMENT list
        if meta_name == "COMMENT":
            if isinstance(value, list):
                lines.extend(CommentLine(text=c) for c in value)
            else:
                lines.append(CommentLine(text=str(value)))
            continue

        # USER_DEFINED list
        if meta_name == "USER_DEFINED":
            lines.extend(_write_user_defined(value))
            continue

        # UPPER_CASE leaf keyword
        if meta_name and meta_name.isupper():
            lines.append(_write_leaf(meta_name, value))
            continue

        # camelCase container field or no-name container
        # Insert blank-line separator when requested
        if sep and lines:
            lines.append(BlankLine())

        ftype_raw = hints[f.name]
        is_list_field = getattr(ftype_raw, "__origin__", None) is list

        if is_list_field:
            item_type = _unwrap(ftype_raw.__args__[0])
            handler = (
                schema_reg.get_handler(typing.cast(type, item_type).__name__)
                if dataclasses.is_dataclass(item_type)
                else None
            )

            for i, item in enumerate(value):
                if sep and i > 0:
                    lines.append(BlankLine())
                lines.extend(
                    _dispatch_write(item, item_type, handler, schema_reg, seg_meta)
                )
        elif dataclasses.is_dataclass(value):
            sub_type = type(value)
            handler = schema_reg.get_handler(sub_type.__name__)
            lines.extend(
                _dispatch_write(value, sub_type, handler, schema_reg, seg_meta)
            )

    return lines


def _dispatch_write(obj, obj_type, handler, schema_reg, seg_meta) -> list[KvnLine]:
    """Dispatch a single object to the appropriate writer based on handler."""
    if handler is None:
        return _write_fields(obj, schema_reg)

    write = handler.write

    if write == WRITE_ROTATION_ANGLE or write == WRITE_ROTATION_RATE:
        return _write_rotation_type(obj)
    if write == WRITE_PACKED_STATE:
        packed = _write_state_vector(obj)
        return [packed] if packed else []
    if write == WRITE_PACKED_ATTITUDE:
        template = _get_aem_template_from_meta(seg_meta)
        packed = _write_attitude_state(obj, template)
        return [packed] if packed else []
    if write == WRITE_COVARIANCE:
        return _write_oem_covariance(obj)
    if write == WRITE_TDM_OBS:
        tdm = _write_tdm_observation(obj)
        return [tdm] if tdm else []
    if write == WRITE_PACKED_LINES:
        return _write_packed_lines(obj, schema_reg)

    # WRITE_DEFAULT
    return _write_fields(obj, schema_reg)


# ---------------------------------------------------------------------------
# Leaf value writer
# ---------------------------------------------------------------------------


def _write_leaf(key: str, value) -> KvLine:
    """Convert a single leaf value to a KvLine."""
    if isinstance(value, Enum):
        return KvLine(key=key, value=value.value)
    if isinstance(value, Decimal):
        return KvLine(key=key, value=str(value))
    if isinstance(value, (str, int, float)):
        return KvLine(key=key, value=str(value))

    # Dataclass with value + optional units (e.g. PositionType, AngleType)
    if dataclasses.is_dataclass(value):
        return _write_value_with_units(key, value)

    return KvLine(key=key, value=str(value))


def _write_value_with_units(key: str, obj) -> KvLine:
    """Convert a value-type dataclass (value + optional units) to KvLine."""
    val_str = str(getattr(obj, "value"))
    unit_str = ""

    for f in dataclasses.fields(obj):
        if f.metadata.get("type") == "Attribute" and f.name == "units":
            unit_val = getattr(obj, f.name)
            if unit_val is not None:
                unit_str = (
                    unit_val.value if isinstance(unit_val, Enum) else str(unit_val)
                )
            break

    return KvLine(key=key, value=val_str, unit=unit_str)


# ---------------------------------------------------------------------------
# User-defined parameters
# ---------------------------------------------------------------------------


def _write_user_defined(ud_list) -> list[KvnLine]:
    """Serialise USER_DEFINED parameters."""
    lines: list[KvnLine] = []
    for param in ud_list:
        lines.append(
            KvLine(key=f"USER_DEFINED_{param.parameter}", value=param.value or "")
        )
    return lines


# ---------------------------------------------------------------------------
# Rotation type writer
# ---------------------------------------------------------------------------


def _write_rotation_type(rot_obj) -> list[KvnLine]:
    """Write a RotationAngleType or RotationRateType as KvLine list.

    Each component (rotation1/2/3) has a ``value``, an ``angle``/``rate``
    attribute (gives the keyword), and optional ``units``.
    """
    lines: list[KvnLine] = []
    for f in dataclasses.fields(rot_obj):
        comp = getattr(rot_obj, f.name)
        if comp is None:
            continue

        kw = None
        unit_str = ""
        for cf in dataclasses.fields(comp):
            if cf.name in ("angle", "rate"):
                kw_enum = getattr(comp, cf.name)
                kw = kw_enum.value if isinstance(kw_enum, Enum) else str(kw_enum)
            elif cf.name == "units":
                unit_val = getattr(comp, cf.name)
                if unit_val is not None:
                    unit_str = (
                        unit_val.value if isinstance(unit_val, Enum) else str(unit_val)
                    )

        if kw:
            lines.append(KvLine(key=kw, value=str(comp.value), unit=unit_str))
    return lines


# ---------------------------------------------------------------------------
# OEM packed state vector writer
# ---------------------------------------------------------------------------


def _write_state_vector(sv) -> PackedDataLine:
    """Convert a StateVectorAccType to a PackedDataLine."""
    tokens = [sv.epoch]
    for fname in (
        "x",
        "y",
        "z",
        "x_dot",
        "y_dot",
        "z_dot",
        "x_ddot",
        "y_ddot",
        "z_ddot",
    ):
        val = getattr(sv, fname, None)
        if val is not None:
            val_str = (
                str(getattr(val, "value"))
                if dataclasses.is_dataclass(val)
                else str(val)
            )
            tokens.append(val_str)
    return PackedDataLine(epoch=sv.epoch, tokens=tokens)


# ---------------------------------------------------------------------------
# OEM covariance writer
# ---------------------------------------------------------------------------


def _write_oem_covariance(cov) -> list[KvnLine]:
    """Write an OemCovarianceMatrixType as KVN lines."""
    lines: list[KvnLine] = []

    # Comments
    for c in cov.comment:
        lines.append(CommentLine(text=c))

    # EPOCH
    lines.append(KvLine(key="EPOCH", value=cov.epoch))

    # COV_REF_FRAME (optional)
    if cov.cov_ref_frame is not None:
        val = cov.cov_ref_frame
        lines.append(
            KvLine(
                key="COV_REF_FRAME",
                value=val.value if isinstance(val, Enum) else str(val),
            )
        )

    # Covariance matrix values — extract all UPPER_CASE value-type fields
    # after the header fields (COMMENT, EPOCH, COV_REF_FRAME)
    _header_names = {"COMMENT", "EPOCH", "COV_REF_FRAME"}
    cov_values: list[str] = []
    for f in dataclasses.fields(cov):
        meta_name = f.metadata.get("name", "")
        if meta_name.isupper() and meta_name not in _header_names:
            val = getattr(cov, f.name)
            if val is not None:
                val_str = (
                    str(getattr(val, "value"))
                    if dataclasses.is_dataclass(val)
                    else str(val)
                )
                cov_values.append(val_str)

    # Write as lower-triangular rows: 1, 2, 3, 4, 5, 6 values per row
    idx = 0
    for row_len in range(1, 7):
        row_tokens = cov_values[idx : idx + row_len]
        if row_tokens:
            lines.append(CovarianceRowLine(tokens=row_tokens))
        idx += row_len

    return lines


# ---------------------------------------------------------------------------
# AEM packed attitude writer
# ---------------------------------------------------------------------------


def _get_aem_template_from_meta(seg_meta) -> list[str]:
    """Derive AEM packed-data column template from segment metadata object."""
    if seg_meta is None:
        return ["EPOCH"]

    kv_lines: list[KvLine] = []
    for f in dataclasses.fields(seg_meta):
        meta_name = f.metadata.get("name", "")
        if not meta_name or not meta_name.isupper():
            continue
        val = getattr(seg_meta, f.name)
        if val is not None:
            val_str = val.value if isinstance(val, Enum) else str(val)
            kv_lines.append(KvLine(key=meta_name, value=val_str))

    return _att_column_template(kv_lines)


def _write_attitude_state(att_state, template: list[str]) -> PackedDataLine | None:
    """Convert an AttitudeStateType to a PackedDataLine using the column template."""
    # Find the one non-None sub-field
    active_sub = None
    for f in dataclasses.fields(att_state):
        val = getattr(att_state, f.name)
        if val is not None:
            active_sub = val
            break

    if active_sub is None:
        return None

    kv_pairs = _collect_att_kv_pairs(active_sub)

    # Build the token list matching the template.
    remaining = list(kv_pairs)
    tokens: list[str] = []
    for kw in template:
        for i, (rk, rv) in enumerate(remaining):
            if rk == kw:
                tokens.append(rv)
                remaining.pop(i)
                break
        else:
            tokens.append("")

    epoch = tokens[0] if tokens else ""
    return PackedDataLine(epoch=epoch, tokens=tokens)


def _collect_att_kv_pairs(obj) -> list[tuple[str, str]]:
    """Recursively collect (keyword, value-string) pairs from an attitude sub-type."""
    pairs: list[tuple[str, str]] = []
    if not dataclasses.is_dataclass(obj):
        return pairs

    cls_name = type(obj).__name__

    # Handle rotation types (RotationAngleType / RotationRateType)
    if cls_name in ("RotationAngleType", "RotationRateType"):
        for f in dataclasses.fields(obj):
            comp = getattr(obj, f.name)
            if comp is not None:
                kw = None
                for cf in dataclasses.fields(comp):
                    if cf.name in ("angle", "rate"):
                        kw_enum = getattr(comp, cf.name)
                        kw = (
                            kw_enum.value if isinstance(kw_enum, Enum) else str(kw_enum)
                        )
                        break
                if kw:
                    pairs.append((kw, str(getattr(comp, "value"))))
        return pairs

    for f in dataclasses.fields(obj):
        val = getattr(obj, f.name)
        if val is None:
            continue

        meta_type = f.metadata.get("type", "")
        if meta_type == "Attribute":
            continue

        meta_name = f.metadata.get("name")

        if meta_name and meta_name.isupper():
            if dataclasses.is_dataclass(val):
                pairs.append((meta_name, str(getattr(val, "value"))))
            elif isinstance(val, Enum):
                pairs.append((meta_name, val.value))
            else:
                pairs.append((meta_name, str(val)))
        elif dataclasses.is_dataclass(val):
            pairs.extend(_collect_att_kv_pairs(val))

    return pairs


# ---------------------------------------------------------------------------
# TDM observation writer
# ---------------------------------------------------------------------------


def _write_tdm_observation(obs) -> TdmObsLine | None:
    """Convert a TrackingDataObservationType to a TdmObsLine."""
    epoch = obs.epoch

    for f in dataclasses.fields(obs):
        if f.name == "epoch":
            continue
        if f.metadata.get("type") == "Attribute":
            continue

        val = getattr(obs, f.name)
        if val is None:
            continue

        meta_name = f.metadata.get("name", f.name.upper())
        if dataclasses.is_dataclass(val):
            val_str = str(getattr(val, "value"))
        elif isinstance(val, Enum):
            val_str = val.value
        elif isinstance(val, Decimal):
            val_str = str(val)
        else:
            val_str = str(val)

        return TdmObsLine(key=meta_name, epoch=epoch, value=val_str)

    return None


# ---------------------------------------------------------------------------
# Packed lines writer (OCM/ACM mixed blocks)
# ---------------------------------------------------------------------------


def _write_packed_lines(obj, schema_reg) -> list[KvnLine]:
    """Write a mixed KEY=VALUE + packed list block (OCM/ACM types).

    Emits the KEY=VALUE header fields first, then one text line per entry
    in the embedded ``list[str]`` field.
    """
    lines: list[KvnLine] = []
    hints = _hints(type(obj))
    packed_values: list[str] | None = None

    for f in dataclasses.fields(obj):
        value = getattr(obj, f.name)
        if value is None:
            continue

        if f.metadata.get("type") == "Attribute":
            continue

        meta_name = f.metadata.get("name")

        # Check if this is the packed list[str] field
        ftype_raw = hints[f.name]
        is_list_field = getattr(ftype_raw, "__origin__", None) is list
        if is_list_field:
            item_type = _unwrap(ftype_raw.__args__[0])
            if item_type is str:
                packed_values = value
                continue

        # COMMENT
        if meta_name == "COMMENT":
            if isinstance(value, list):
                lines.extend(CommentLine(text=c) for c in value)
            else:
                lines.append(CommentLine(text=str(value)))
            continue

        # UPPER_CASE leaf
        if meta_name and meta_name.isupper():
            lines.append(_write_leaf(meta_name, value))
            continue

    # Emit packed lines
    if packed_values:
        for packed_line in packed_values:
            lines.append(KvLine(key="", value=packed_line))

    return lines
