# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
KVN writer: serialise an xsdata dataclass tree to a list of
:class:`~ccsds_ndm.kvn_utils_tokenizer.KvnLine` objects.

This is the inverse of :mod:`ccsds_ndm.kvn_utils_builder`.  The public
entry point is :func:`write_kvn_lines`.
"""

import dataclasses
from decimal import Decimal
from enum import Enum

from ccsds_ndm.kvn_utils_builder import _hints, _unwrap
from ccsds_ndm.kvn_utils_tokenizer import (
    BlankLine,
    CommentLine,
    CovarianceRowLine,
    KvLine,
    KvnLine,
    PackedDataLine,
    SectionMarkerLine,
    TdmObsLine,
)

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
    # Version line
    lines: list[KvnLine] = [KvLine(key=ndm_obj.id, value=ndm_obj.version)]

    # Determine document structure
    body_hints = _hints(_unwrap(_hints(type(ndm_obj))["body"]))

    seg_raw = body_hints["segment"]
    is_list_segment = getattr(seg_raw, "__origin__", None) is list

    if "relative_metadata_data" in body_hints:
        # CDM
        lines.extend(_write_cdm(ndm_obj, body_hints))
    elif is_list_segment:
        # Segment-based (OEM, AEM, TDM)
        data_clazz = _unwrap(_hints(_unwrap(seg_raw.__args__[0]))["data"])
        lines.extend(_write_segment_based(ndm_obj, data_clazz))
    else:
        # Flat (OPM, OMM, APM, RDM)
        data_clazz = _unwrap(_hints(_unwrap(seg_raw))["data"])
        lines.extend(_write_flat(ndm_obj, data_clazz))

    return lines


# ---------------------------------------------------------------------------
# Flat types (OPM, OMM, APM, RDM)
# ---------------------------------------------------------------------------


def _write_flat(ndm_obj, data_clazz) -> list[KvnLine]:
    lines: list[KvnLine] = []
    lines.append(BlankLine())
    lines.extend(_write_fields(ndm_obj.header))
    lines.append(BlankLine())
    seg = ndm_obj.body.segment
    lines.extend(_write_fields(seg.metadata))
    lines.append(BlankLine())
    lines.extend(_write_data(seg.data, data_clazz))
    return lines


# ---------------------------------------------------------------------------
# Segment-based types (OEM, AEM, TDM)
# ---------------------------------------------------------------------------


def _write_segment_based(ndm_obj, data_clazz) -> list[KvnLine]:
    lines: list[KvnLine] = []
    lines.append(BlankLine())
    lines.extend(_write_fields(ndm_obj.header))
    lines.append(BlankLine())

    data_cls_name = data_clazz.__name__

    for seg in ndm_obj.body.segment:
        # META block
        lines.append(SectionMarkerLine(key="META_START"))
        lines.extend(_write_fields(seg.metadata))
        lines.append(SectionMarkerLine(key="META_STOP"))
        lines.append(BlankLine())

        if data_cls_name in ("AemData", "TdmData"):
            lines.append(SectionMarkerLine(key="DATA_START"))

        # Data
        lines.extend(_write_data(seg.data, data_clazz, seg_meta=seg.metadata))

        if data_cls_name in ("AemData", "TdmData"):
            lines.append(SectionMarkerLine(key="DATA_STOP"))

        # OEM covariance
        if data_cls_name == "OemData" and seg.data.covariance_matrix:
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


def _write_cdm(ndm_obj, body_hints) -> list[KvnLine]:
    lines: list[KvnLine] = []
    body = ndm_obj.body

    # Header
    lines.append(BlankLine())
    lines.extend(_write_fields(ndm_obj.header))
    lines.append(BlankLine())

    # Relative metadata
    lines.extend(
        _write_data(body.relative_metadata_data, type(body.relative_metadata_data))
    )
    lines.append(BlankLine())

    # Object segments
    seg_raw = body_hints["segment"]
    is_list_seg = getattr(seg_raw, "__origin__", None) is list
    segments = body.segment if is_list_seg else [body.segment]

    for seg in segments:
        data_clazz = _unwrap(_hints(type(seg))["data"])
        lines.extend(_write_fields(seg.metadata))
        lines.append(BlankLine())
        lines.extend(_write_data(seg.data, data_clazz))
        lines.append(BlankLine())

    return lines


# ---------------------------------------------------------------------------
# Core recursive field writer
# ---------------------------------------------------------------------------


def _write_fields(obj, *, sep: bool = False) -> list[KvnLine]:
    """Recursively serialize an xsdata dataclass to KvnLines.

    Parameters
    ----------
    obj : object
        An xsdata dataclass instance.
    sep : bool
        If *True*, insert :class:`BlankLine` separators before each
        camelCase sub-container field.  Used for flat-type data sections
        so that the reader's forward-looking comment assignment works
        correctly on round-trip.
    """
    if obj is None:
        return []
    cls = type(obj)
    if not dataclasses.is_dataclass(cls):
        return []

    hints = _hints(cls)
    lines: list[KvnLine] = []

    for f in dataclasses.fields(cls):
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
        # Insert blank-line separator when requested (flat-type data sections)
        if sep and lines:
            lines.append(BlankLine())

        ftype_raw = hints[f.name]
        is_list_field = getattr(ftype_raw, "__origin__", None) is list

        if is_list_field:
            for i, item in enumerate(value):
                if sep and i > 0:
                    lines.append(BlankLine())
                lines.extend(_write_fields(item, sep=sep))
        elif dataclasses.is_dataclass(value):
            # Handle rotation types specially
            cls_name = type(value).__name__
            if cls_name in ("RotationAngleType", "RotationRateType"):
                lines.extend(_write_rotation_type(value))
            else:
                lines.extend(_write_fields(value, sep=sep))

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

        # Find the keyword from the angle/rate discriminator attribute
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
    """Serialize USER_DEFINED parameters."""
    lines: list[KvnLine] = []
    for param in ud_list:
        lines.append(
            KvLine(key=f"USER_DEFINED_{param.parameter}", value=param.value or "")
        )
    return lines


# ---------------------------------------------------------------------------
# Data section writer (dispatches to special types)
# ---------------------------------------------------------------------------


def _write_data(data_obj, data_clazz, seg_meta=None) -> list[KvnLine]:
    """Write a data section, handling special packed data types."""
    cls_name = data_clazz.__name__

    if cls_name == "OemData":
        return _write_oem_data(data_obj)
    if cls_name == "AemData":
        return _write_aem_data(data_obj, seg_meta)
    if cls_name == "TdmData":
        return _write_tdm_data(data_obj)

    # Generic: use recursive field writer (handles OPM, OMM, APM, RDM, CDM data)
    # sep=True inserts blank lines between sub-containers so the reader's
    # forward-looking comment assignment works on round-trip.
    return _write_fields(data_obj, sep=True)


# ---------------------------------------------------------------------------
# OEM special writers
# ---------------------------------------------------------------------------


def _write_oem_data(data_obj) -> list[KvnLine]:
    """Write OEM data: comments + packed state vectors."""
    lines: list[KvnLine] = []

    # Comments
    for c in data_obj.comment:
        lines.append(CommentLine(text=c))

    # State vectors as packed data lines
    for sv in data_obj.state_vector:
        lines.append(_write_state_vector(sv))

    return lines


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
# AEM special writers
# ---------------------------------------------------------------------------


def _write_aem_data(data_obj, seg_meta) -> list[KvnLine]:
    """Write AEM data: comments + packed attitude state lines."""
    lines: list[KvnLine] = []

    # Comments
    for c in data_obj.comment:
        lines.append(CommentLine(text=c))

    # Determine column template from metadata
    template = _get_aem_template_from_meta(seg_meta)

    # Attitude states as packed data lines
    for att_state in data_obj.attitude_state:
        packed = _write_attitude_state(att_state, template)
        if packed:
            lines.append(packed)

    return lines


def _get_aem_template_from_meta(seg_meta) -> list[str]:
    """Derive AEM packed-data column template from segment metadata object."""
    if seg_meta is None:
        return ["EPOCH"]

    # Build a KvLine-like representation for _att_column_template
    from collections.abc import Sequence

    from ccsds_ndm.kvn_utils_builder import _att_column_template

    kv_lines: Sequence[KvLine] = []
    for f in dataclasses.fields(seg_meta):
        meta_name = f.metadata.get("name", "")
        if not meta_name or not meta_name.isupper():
            continue
        val = getattr(seg_meta, f.name)
        if val is not None:
            val_str = val.value if isinstance(val, Enum) else str(val)
            kv_lines = [*kv_lines, KvLine(key=meta_name, value=val_str)]

    return _att_column_template(kv_lines)  # type: ignore[arg-type]


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

    # Collect tokens as an ordered (keyword, value) list — preserving
    # duplicates so that e.g. (Y_RATE, v1), (X_RATE, v2), (Y_RATE, v3)
    # can be matched positionally to the template.
    kv_pairs = _collect_att_kv_pairs(active_sub)

    # Build the token list matching the template.
    # For unique keywords a simple lookup suffices; for duplicates we
    # consume the pairs in order (each template slot pops the first
    # remaining pair with a matching keyword).
    remaining = list(kv_pairs)  # mutable copy
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
    """Recursively collect (keyword, value-string) pairs from an attitude sub-type.

    Unlike a dict, this preserves duplicate keywords (e.g. two Y_RATE
    entries for EULER_ROT_SEQ = 212).
    """
    pairs: list[tuple[str, str]] = []
    if not dataclasses.is_dataclass(obj):
        return pairs

    cls = type(obj)
    cls_name = cls.__name__

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
# TDM special writers
# ---------------------------------------------------------------------------


def _write_tdm_data(data_obj) -> list[KvnLine]:
    """Write TDM data: comments + observation lines."""
    lines: list[KvnLine] = []

    # Comments
    for c in data_obj.comment:
        lines.append(CommentLine(text=c))

    # Observations
    for obs in data_obj.observation:
        tdm_line = _write_tdm_observation(obs)
        if tdm_line:
            lines.append(tdm_line)

    return lines


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
