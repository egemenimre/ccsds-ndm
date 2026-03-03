# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
KVN object builder: mapping a :class:`~ccsds_ndm.kvn_utils_parser.KvnDocument`
onto the xsdata dataclass tree for the detected NDM type.

This module contains the object-construction stage of the KVN read pipeline.
The tokenise and block-split stages live in their own modules:

- :mod:`ccsds_ndm.kvn_utils_tokenizer` — line classification (:func:`tokenize`)
- :mod:`ccsds_ndm.kvn_utils_parser` — document assembly (:func:`parse_blocks`)

Re-exports
----------
For backwards compatibility all public names from the two upstream modules are
re-exported here so that existing ``from ccsds_ndm.kvn_utils_builder import …``
statements continue to work without change.
"""

import dataclasses
import types as _types
import typing

from ccsds_ndm.kvn_utils import (
    _lenient_class_factory,
    build_ndm_object,
    get_ccsds_kw_list,
    init_root_ndm_object,
)
from ccsds_ndm.kvn_utils_parser import KvnDocument  # noqa: F401  (re-export)
from ccsds_ndm.kvn_utils_tokenizer import (  # noqa: F401  (re-export)
    BlankLine,
    CommentLine,
    CovarianceRowLine,
    KvLine,
    KvnLine,
    PackedDataLine,
    TdmObsLine,
)

# Hard-coded keywords for RotationAngleType / RotationRateType
# (their fields have name=None, so get_ccsds_kw_list returns [])
_ROTATION_KWS: dict[str, list[str]] = {
    "RotationAngleType": ["X_ANGLE", "Y_ANGLE", "Z_ANGLE"],
    "RotationRateType": ["X_RATE", "Y_RATE", "Z_RATE"],
}

# ---------------------------------------------------------------------------
# Object builder — utility helpers
# ---------------------------------------------------------------------------


def _kvlines_to_rows(lines: list[KvnLine]) -> list[list[str]]:
    """
    Convert a list of :class:`KvnLine` objects to the ``[key, value(, unit)]``
    row format expected by the production :func:`~ccsds_ndm.kvn_utils.build_ndm_object`.

    Only :class:`KvLine` and :class:`CommentLine` produce rows; all other line
    types (blank, packed-data, covariance-row, section-marker) are skipped.
    """
    rows: list[list[str]] = []
    for line in lines:
        if isinstance(line, KvLine):
            row: list[str] = [line.key, line.value]
            if line.unit:
                row.append(line.unit)
            rows.append(row)
        elif isinstance(line, CommentLine):
            rows.append(["COMMENT", line.text])
    return rows


def _att_column_template(meta_lines: list[KvnLine]) -> list[str]:
    """
    Derive the packed-data column template for an AEM segment from its
    metadata lines.

    Returns a list of KVN keyword strings giving the column order, e.g.
    ``["EPOCH", "Q1", "Q2", "Q3", "QC"]``.  The first element is always
    ``"EPOCH"``.

    Parameters
    ----------
    meta_lines : list[KvnLine]
        The ``KvnBlock.meta`` list for one AEM segment.
    """
    kv: dict[str, str] = {}
    for line in meta_lines:
        if isinstance(line, KvLine):
            kv[line.key] = line.value

    att_type = kv.get("ATTITUDE_TYPE", "")
    quat_type = kv.get("QUATERNION_TYPE", "FIRST").upper()
    rot_seq = kv.get("EULER_ROT_SEQ", "")

    # Axis-index → angle/rate keyword maps
    _angle = {"1": "X_ANGLE", "2": "Y_ANGLE", "3": "Z_ANGLE"}
    _rate = {"1": "X_RATE", "2": "Y_RATE", "3": "Z_RATE"}

    att_upper = att_type.upper().replace(" ", "")

    if att_upper in ("QUATERNION", "QUATERNION_1"):
        if quat_type == "LAST":
            return ["EPOCH", "Q1", "Q2", "Q3", "QC"]
        return ["EPOCH", "QC", "Q1", "Q2", "Q3"]

    if att_upper in ("QUATERNION/DERIVATIVE", "QUATERNION_DERIVATIVE"):
        if quat_type == "LAST":
            base = [
                "EPOCH",
                "Q1",
                "Q2",
                "Q3",
                "QC",
                "Q1_DOT",
                "Q2_DOT",
                "Q3_DOT",
                "QC_DOT",
            ]
        else:
            base = [
                "EPOCH",
                "QC",
                "Q1",
                "Q2",
                "Q3",
                "QC_DOT",
                "Q1_DOT",
                "Q2_DOT",
                "Q3_DOT",
            ]
        return base

    if att_upper in ("QUATERNION/RATE", "QUATERNION_RATE"):
        rates = [_rate[d] for d in rot_seq if d in _rate]
        if quat_type == "LAST":
            return ["EPOCH", "Q1", "Q2", "Q3", "QC"] + rates
        return ["EPOCH", "QC", "Q1", "Q2", "Q3"] + rates

    if att_upper in ("EULER_ANGLE", "EULER_ANGLE_1"):
        angles = [_angle[d] for d in rot_seq if d in _angle]
        return ["EPOCH"] + angles

    if att_upper in ("EULER_ANGLE/RATE", "EULER_ANGLE_RATE"):
        angles = [_angle[d] for d in rot_seq if d in _angle]
        rates = [_rate[d] for d in rot_seq if d in _rate]
        return ["EPOCH"] + angles + rates

    if att_upper in ("SPIN", "SPIN_1"):
        return ["EPOCH", "SPIN_ALPHA", "SPIN_DELTA", "SPIN_ANGLE", "SPIN_ANGLE_VEL"]

    if att_upper in ("SPIN/NUTATION", "SPIN_NUTATION"):
        return [
            "EPOCH",
            "SPIN_ALPHA",
            "SPIN_DELTA",
            "SPIN_ANGLE",
            "SPIN_ANGLE_VEL",
            "NUTATION",
            "NUTATION_PER",
            "NUTATION_PHASE",
        ]

    # Fallback — return just epoch
    return ["EPOCH"]


def _hints(cls) -> dict:
    """Return the resolved type hints for *cls*."""
    return typing.get_type_hints(cls)


def _unwrap(t) -> typing.Any:
    """Strip ``Optional[X]`` → ``X``; return *t* unchanged otherwise."""
    origin = getattr(t, "__origin__", None)
    if origin is _types.UnionType or origin is typing.Union:
        args = [a for a in t.__args__ if a is not type(None)]
        return args[0] if args else str
    return t


def _collect_all_kws(cls) -> list[str]:
    """
    Return all KVN keywords reachable from *cls*, recursing into
    no-``"name"`` sub-containers and camelCase container fields.
    """
    if cls.__name__ in _ROTATION_KWS:
        return list(_ROTATION_KWS[cls.__name__])
    kws = []
    hints = _hints(cls)
    for f in dataclasses.fields(cls):
        meta_name = f.metadata.get("name")
        if meta_name is None or meta_name == "":
            # No-name sub-container: expand its keywords directly
            ftype = _unwrap(hints[f.name])
            if dataclasses.is_dataclass(ftype):
                kws.extend(_collect_all_kws(ftype))
        elif not meta_name.isupper():
            # camelCase container field: recurse to get its keywords
            ftype_raw = hints[f.name]
            is_list_field = getattr(ftype_raw, "__origin__", None) is list
            if is_list_field:
                ftype = _unwrap(ftype_raw.__args__[0])
            else:
                ftype = _unwrap(ftype_raw)
            if dataclasses.is_dataclass(ftype):
                kws.extend(_collect_all_kws(ftype))
        else:
            kws.append(meta_name)
    return kws


def _has_field(cls, name: str) -> bool:
    """Return ``True`` if *cls* has a dataclass field named *name*."""
    return any(f.name == name for f in dataclasses.fields(cls))


def _build_rotation_type(rot_clazz, inst_lines: list[KvnLine]) -> object:
    """Build a ``RotationAngleType`` or ``RotationRateType`` from ordered KvnLines."""
    rot_hints = _hints(rot_clazz)
    rot_fields = dataclasses.fields(rot_clazz)  # rotation1, rotation2, rotation3
    kv_rows = [
        (ln.key, ln.value, ln.unit) for ln in inst_lines if isinstance(ln, KvLine)
    ]
    params = {}
    for rf, (kw, val, unit) in zip(rot_fields, kv_rows):
        comp_type = _unwrap(rot_hints[rf.name])
        comp_hints = _hints(comp_type)
        comp_fields = dataclasses.fields(comp_type)
        value_field = comp_fields[0]
        angle_field = comp_fields[1]
        units_field = next(
            (
                f
                for f in comp_fields
                if f.metadata.get("type") == "Attribute" and f.name == "units"
            ),
            None,
        )
        angle_type = _unwrap(comp_hints[angle_field.name])
        comp_params = {
            value_field.name: float(val),
            angle_field.name: angle_type(kw),
        }
        if units_field and unit:
            units_type = _unwrap(comp_hints[units_field.name])
            try:
                comp_params[units_field.name] = units_type(unit.strip())
            except (ValueError, KeyError):
                pass
        params[rf.name] = comp_type(**comp_params)
    return _lenient_class_factory(rot_clazz, params)


def _label_lines(
    all_lines: list[KvnLine],
    container_map: dict[str, tuple[str, type, bool]],
) -> list[str | None]:
    """
    Assign a label to every line in *all_lines*.

    Returns a parallel list of label strings (or ``None`` for
    :class:`BlankLine`\\s).  Each label is either ``"own"`` (the line belongs
    to the data class itself) or a field name string (the line belongs to a
    camelCase sub-container).

    Two passes are applied:

    1. **KvLine pass** — :class:`KvLine`\\s are labelled directly from
       *container_map*; ``USER_DEFINED_*`` keys and unknown keys get ``"own"``.
    2. **Forward-looking pass** — unlabelled lines (:class:`CommentLine` and
       other non-blank types) look ahead to the next labelled line.  If no
       blank line intervenes, the comment inherits that label; otherwise it
       falls back to ``"own"``.
    """
    n = len(all_lines)
    labels: list[str | None] = [None] * n

    # Pass 1: label KvLines by keyword membership
    for i, ln in enumerate(all_lines):
        if isinstance(ln, KvLine):
            kw = ln.key
            if kw.startswith("USER_DEFINED_") or kw not in container_map:
                labels[i] = "own"
            else:
                labels[i] = container_map[kw][0]  # field name

    # Pass 2: forward-looking assignment for unlabelled lines
    for i in range(n):
        if labels[i] is not None or isinstance(all_lines[i], BlankLine):
            continue
        has_blank = False
        next_label: str | None = None
        for j in range(i + 1, n):
            if isinstance(all_lines[j], BlankLine):
                has_blank = True
            elif labels[j] is not None:
                next_label = labels[j]
                break
        labels[i] = next_label if (next_label is not None and not has_blank) else "own"

    return labels


def _partition_lines(
    all_lines: list[KvnLine],
    labels: list[str | None],
    container_map: dict[str, tuple[str, type, bool]],
    list_first_kw: dict[str, str],
) -> tuple[list[KvnLine], dict[str, list[list[KvnLine]]]]:
    """
    Partition lines into "own" and per-container buckets using labels.

    Returns a tuple of (own_lines, container_buckets):
    - *own_lines*: Lines labelled ``"own"`` (belong to the data class itself).
    - *container_buckets*: Dict mapping field name → list of line-group buckets
      for list fields, or a single bucket for scalar fields.
    """
    own_lines: list[KvnLine] = []
    container_buckets: dict[str, list[list[KvnLine]]] = {}

    for i, ln in enumerate(all_lines):
        if isinstance(ln, BlankLine):
            continue
        lbl = labels[i]
        if lbl == "own":
            own_lines.append(ln)
            continue

        assert lbl is not None  # Already checked: not blank, not "own"
        fname = lbl
        if isinstance(ln, KvLine) and ln.key in container_map:
            _, sub_clazz, is_list = container_map[ln.key]
            if is_list:
                first_kw = list_first_kw.get(fname)
                buckets = container_buckets.setdefault(fname, [])
                if ln.key == first_kw or not buckets:
                    # Start new instance. Move any trailing COMMENTs
                    # from the previous bucket into the new one (they
                    # belong to this instance per forward-looking rule).
                    stolen: list[KvnLine] = []
                    if buckets and buckets[-1]:
                        while buckets[-1] and isinstance(buckets[-1][-1], CommentLine):
                            stolen.append(buckets[-1].pop())
                        if not buckets[-1]:
                            buckets.pop()  # remove empty bucket
                        stolen.reverse()
                    buckets.append(stolen + [ln])
                else:
                    buckets[-1].append(ln)
            else:
                buckets = container_buckets.setdefault(fname, [[]])
                buckets[-1].append(ln)
        else:
            # CommentLine or other non-KvLine assigned to a container
            buckets = container_buckets.setdefault(fname, [])
            if not buckets:
                buckets.append([ln])
            else:
                buckets[-1].append(ln)

    return own_lines, container_buckets


def _build_nested_data(data_cls, all_lines: list[KvnLine]) -> object:
    """
    Build a data object whose fields include camelCase sub-containers.

    Partitions flat KvnLines into per-container buckets by keyword membership,
    builds each sub-container with :func:`build_ndm_object` or a specialised
    builder, and attaches the results to the data object.

    High-level flow:
    1. Inspect *data_cls* to identify camelCase sub-container fields and their
       associated KVN keywords.  Build a reverse map from keyword → container.
    2. Label each line in *all_lines* to determine which container (or the data
       class itself) it belongs to.
    3. Partition lines into "own" (direct data class keywords) and per-container
       buckets.
    4. Build the data class from "own" lines.
    5. Build and attach each camelCase sub-container from its bucket.
    6. Build and attach any no-``"name"`` nested structures (e.g. quaternions).
    7. Build and attach USER_DEFINED parameters if present.
    """
    data_hints_local = _hints(data_cls)

    # --- Step 1: Build keyword → (field_name, sub_clazz, is_list) map ---
    # For each camelCase field in *data_cls*, collect all keywords it accepts
    # and build a reverse map: keyword → which field it belongs to.
    container_map: dict[str, tuple[str, type, bool]] = {}
    list_first_kw: dict[str, str] = {}  # first keyword per list field (marks start)

    for f in dataclasses.fields(data_cls):
        meta_name = f.metadata.get("name", "")
        if not meta_name or meta_name.isupper():
            continue  # Skip direct keywords and no-name fields

        ftype_raw = data_hints_local[f.name]
        is_list_field = getattr(ftype_raw, "__origin__", None) is list
        if is_list_field:
            # List field: can contain multiple instances (e.g. [Maneuver])
            item_type = _unwrap(ftype_raw.__args__[0])
            kws = _collect_all_kws(item_type)
            for kw in kws:
                if kw and kw != "COMMENT":
                    container_map[kw] = (f.name, item_type, True)
            first = next((k for k in kws if k and k != "COMMENT"), None)
            if first:
                list_first_kw[f.name] = first  # Track first kw to detect new instance
        else:
            # Scalar field: single instance (e.g. spacecraft_parameters)
            sub_clazz = _unwrap(ftype_raw)
            kws = _collect_all_kws(sub_clazz)
            for kw in kws:
                if kw and kw != "COMMENT":
                    container_map[kw] = (f.name, sub_clazz, False)

    # --- Step 2: Assign a label to every line in *all_lines* ---
    # Each line is labeled either "own" (belongs to data_cls directly) or
    # a field name string (belongs to a camelCase sub-container).
    labels = _label_lines(all_lines, container_map)

    # --- Step 3: Partition lines using labels ---
    # Split *all_lines* into "own" (for the data class) and per-container
    # buckets for building sub-objects.
    own_lines, container_buckets = _partition_lines(
        all_lines, labels, container_map, list_first_kw
    )

    # --- Step 4: Build data object from own_rows ---
    # Convert "own" lines to [key, value, (unit)] rows and construct the
    # data class using the standard builder.
    own_rows = _kvlines_to_rows(own_lines)
    seg_data = build_ndm_object(data_cls, own_rows)

    # --- Step 5: Handle no-"name" sub-containers (e.g. QuaternionType) ---
    # Some fields have metadata.name=None or "", meaning they are "transparent"
    # containers whose keywords are directly in the parent class.  These must
    # be built from the same "own" rows and attached to the parent object.
    # Example: QuaternionStateType has a nested QuaternionType with no name.
    for f in dataclasses.fields(data_cls):
        meta_name = f.metadata.get("name")
        if (meta_name is None or meta_name == "") and dataclasses.is_dataclass(
            _unwrap(data_hints_local[f.name])
        ):
            inner_clazz = _unwrap(data_hints_local[f.name])
            inner_obj = build_ndm_object(inner_clazz, own_rows)
            setattr(seg_data, f.name, inner_obj)

    # --- Step 6: Build and attach each camelCase sub-container ---
    # For each camelCase field (with a proper name), build its sub-object(s)
    # from the corresponding bucket of lines and attach to the data object.
    # List fields get a list of built objects; scalar fields get a single object.
    for f in dataclasses.fields(data_cls):
        meta_name = f.metadata.get("name", "")
        if not meta_name or meta_name.isupper():
            continue  # Skip direct keywords and no-name fields
        if f.name not in container_buckets:
            continue  # No data for this field

        ftype_raw = data_hints_local[f.name]
        is_list_field = getattr(ftype_raw, "__origin__", None) is list
        buckets = container_buckets[f.name]

        if is_list_field:
            # Build a list of sub-objects, one per bucket (one per instance)
            item_type = _unwrap(ftype_raw.__args__[0])
            built_list = [_build_sub_object(item_type, inst) for inst in buckets]
            setattr(seg_data, f.name, built_list)
        else:
            # Build a single sub-object from the first (and only) bucket
            sub_clazz = _unwrap(ftype_raw)
            inst = buckets[0] if buckets else []
            setattr(seg_data, f.name, _build_sub_object(sub_clazz, inst))

    # --- Step 7: Build and attach USER_DEFINED parameters (if present) ---
    # Some classes support a user_defined_parameters field for arbitrary
    # key-value pairs prefixed "USER_DEFINED_".  Extract those rows and
    # build them separately with the special "USER_DEFINED" prefix.
    ud_field = next(
        (
            f
            for f in dataclasses.fields(data_cls)
            if f.name == "user_defined_parameters"
        ),
        None,
    )
    if ud_field is not None:
        ud_rows = [r for r in own_rows if r[0].startswith("USER_DEFINED_")]
        if ud_rows:
            ud_type = _unwrap(data_hints_local["user_defined_parameters"])
            ud_obj = build_ndm_object(ud_type, ud_rows, prefix="USER_DEFINED")
            setattr(seg_data, "user_defined_parameters", ud_obj)

    return seg_data


def _build_sub_object(sub_clazz, inst_lines: list[KvnLine]) -> object:
    """
    Build a sub-container xsdata object from a flat list of KvnLines.

    Dispatches to :func:`_build_rotation_type` for rotation types,
    :func:`_build_nested_data` for containers with camelCase fields, or
    :func:`~ccsds_ndm.kvn_utils.build_ndm_object` for standard containers.
    """
    clazz_name = sub_clazz.__name__
    if clazz_name in ("RotationAngleType", "RotationRateType"):
        return _build_rotation_type(sub_clazz, inst_lines)

    # Check if this sub-container itself has camelCase container fields
    has_nested = any(
        f.metadata.get("name", "") and not f.metadata["name"].isupper()
        for f in dataclasses.fields(sub_clazz)
    )
    if has_nested:
        return _build_nested_data(sub_clazz, inst_lines)

    # Standard: all UPPER_CASE keywords
    rows = _kvlines_to_rows(inst_lines)
    obj = build_ndm_object(sub_clazz, rows)

    # Handle no-"name" sub-sub-containers (QuaternionType in QuaternionStateType)
    sub_hints = _hints(sub_clazz)
    for f in dataclasses.fields(sub_clazz):
        meta_name = f.metadata.get("name")
        if (meta_name is None or meta_name == "") and dataclasses.is_dataclass(
            _unwrap(sub_hints[f.name])
        ):
            inner_clazz = _unwrap(sub_hints[f.name])
            inner_obj = build_ndm_object(inner_clazz, rows)
            setattr(obj, f.name, inner_obj)

    return obj


def _label_cdm_lines(
    all_lines: list[KvnLine], header_kws: set[str]
) -> list[str | None]:
    """
    Label CDM data lines as "header" or "other" using two-pass approach.

    Pass 1: Label KvLines by header keyword membership.
    Pass 2: Forward-looking for unlabeled lines (COMMENTs, etc.).
    Rule 4: Orphan COMMENTs above first header keyword → "header".
    """
    n = len(all_lines)
    labels: list[str | None] = [None] * n

    # Pass 1: label KvLines
    for i, ln in enumerate(all_lines):
        if isinstance(ln, KvLine):
            labels[i] = "header" if ln.key in header_kws else "other"

    # Pass 2: forward-looking for unlabeled lines
    for i in range(n):
        if labels[i] is not None or isinstance(all_lines[i], BlankLine):
            continue
        has_blank = False
        next_label: str | None = None
        for j in range(i + 1, n):
            if isinstance(all_lines[j], BlankLine):
                has_blank = True
            elif labels[j] is not None:
                next_label = labels[j]
                break
        labels[i] = (
            next_label if (next_label is not None and not has_blank) else "other"
        )

    # Rule 4: orphan COMMENTs above first header keyword → header
    first_hdr = next((i for i, lb in enumerate(labels) if lb == "header"), n)
    for i in range(first_hdr):
        if isinstance(all_lines[i], CommentLine) and labels[i] == "other":
            labels[i] = "header"

    return labels


def _split_cdm_objects(
    all_lines: list[KvnLine], labels: list[str | None], doc_header: list[KvnLine]
) -> tuple[list[KvnLine], list[KvnLine], list[list[KvnLine]]]:
    """
    Split CDM data lines into header, relative metadata, and object segments.

    Objects are delimited by OBJECT keywords. Returns (header_lines, rel_meta_lines, object_splits).
    """
    cdm_hdr_lines: list[KvnLine] = list(doc_header)
    cdm_rel_meta_lines: list[KvnLine] = []
    cdm_obj_splits: list[list[KvnLine]] = []
    cdm_rel_done = False
    current_cdm_obj: list[KvnLine] = []

    for i, ln in enumerate(all_lines):
        if isinstance(ln, BlankLine):
            current_cdm_obj.append(ln)
            continue
        if labels[i] == "header":
            cdm_hdr_lines.append(ln)
        elif isinstance(ln, KvLine) and ln.key == "OBJECT":
            # Move trailing COMMENTs from previous block to this one.
            stolen_comments: list[KvnLine] = []
            while current_cdm_obj and isinstance(
                current_cdm_obj[-1], (CommentLine, BlankLine)
            ):
                stolen_comments.append(current_cdm_obj.pop())
            stolen_comments.reverse()
            if not cdm_rel_done:
                cdm_rel_meta_lines = current_cdm_obj
                cdm_rel_done = True
            else:
                cdm_obj_splits.append(current_cdm_obj)
            current_cdm_obj = stolen_comments + [ln]
        else:
            current_cdm_obj.append(ln)

    if current_cdm_obj:
        if not cdm_rel_done:
            cdm_rel_meta_lines = current_cdm_obj
        else:
            cdm_obj_splits.append(current_cdm_obj)

    return cdm_hdr_lines, cdm_rel_meta_lines, cdm_obj_splits


def _build_cdm_object_segment(
    obj_lines: list[KvnLine],
    meta_kws: set[str],
    meta_clazz,
    data_clazz,
    segment_clazz,
) -> object:
    """
    Build a single CDM object segment from a list of lines.

    Partitions lines into metadata and data by keyword membership,
    then builds and returns the segment object.
    """
    obj_n = len(obj_lines)
    obj_labels: list[str | None] = [None] * obj_n

    # Pass 1: label KvLines by keyword membership
    for idx, ln in enumerate(obj_lines):
        if isinstance(ln, KvLine):
            obj_labels[idx] = "meta" if ln.key in meta_kws else "data"

    # Pass 2: forward-looking for unlabeled lines
    for idx in range(obj_n):
        if obj_labels[idx] is not None or isinstance(obj_lines[idx], BlankLine):
            continue
        has_blank = False
        next_label: str | None = None
        for j in range(idx + 1, obj_n):
            if isinstance(obj_lines[j], BlankLine):
                has_blank = True
            elif obj_labels[j] is not None:
                next_label = obj_labels[j]
                break
        obj_labels[idx] = (
            next_label if (next_label is not None and not has_blank) else "data"
        )

    # Partition lines by label
    obj_meta_lines: list[KvnLine] = []
    obj_data_lines: list[KvnLine] = []
    for idx, ln in enumerate(obj_lines):
        if isinstance(ln, BlankLine):
            obj_data_lines.append(ln)
        elif obj_labels[idx] == "meta":
            obj_meta_lines.append(ln)
        else:
            obj_data_lines.append(ln)

    # Build segment from metadata and data
    seg_meta = build_ndm_object(meta_clazz, _kvlines_to_rows(obj_meta_lines))
    seg_data = _build_nested_data(data_clazz, obj_data_lines)
    return _lenient_class_factory(
        segment_clazz, {"metadata": seg_meta, "data": seg_data}
    )


# ---------------------------------------------------------------------------
# CDM flat-type handler
# ---------------------------------------------------------------------------


def _build_cdm_flat_object(
    doc: KvnDocument,
    header_field_type,
    meta_clazz,
    data_clazz,
    body_field_type,
    segment_clazz,
    header_kws: set[str],
    meta_kws: set[str],
    clazz,
) -> object:
    """
    Build a CDM (Conjunction Data Message) flat-type object.

    CDM has a special two-part structure with relative_metadata_data
    and segments containing relative and primary objects.
    """
    rel_meta_clazz = _unwrap(_hints(body_field_type)["relative_metadata_data"])
    all_data_lines = doc.segments[0].data

    # Label lines as header or other
    cdm_labels = _label_cdm_lines(all_data_lines, header_kws)

    # Split into header lines, relative metadata, and object segments
    cdm_hdr_lines, cdm_rel_meta_lines, cdm_obj_splits = _split_cdm_objects(
        all_data_lines, cdm_labels, doc.header
    )

    # Build header and relative metadata
    ndm_header = build_ndm_object(header_field_type, _kvlines_to_rows(cdm_hdr_lines))
    rel_meta_obj = _build_nested_data(rel_meta_clazz, cdm_rel_meta_lines)

    # Build segments
    built_segments = [
        _build_cdm_object_segment(
            obj_lines, meta_kws, meta_clazz, data_clazz, segment_clazz
        )
        for obj_lines in cdm_obj_splits
    ]

    # Assemble body and return
    ndm_body = _lenient_class_factory(
        body_field_type,
        {
            "relative_metadata_data": rel_meta_obj,
            "segment": built_segments,
        },
    )
    return _lenient_class_factory(clazz, {"header": ndm_header, "body": ndm_body})


def _partition_flat_type_lines(
    all_flat: list[KvnLine], header_kws: set[str], meta_kws: set[str]
) -> tuple[list[KvnLine], list[KvnLine], list[KvnLine]]:
    """
    Partition flat-type document lines into header, metadata, and data sections.

    Uses a two-pass labeling algorithm:
    - Pass 1: Label KvLines by keyword membership
    - Pass 2: Forward-looking assignment for COMMENTs and orphans
    - Pass 3: Apply Rule 4 for orphan COMMENTs above first header keyword

    BlankLines are preserved in the data partition for use as separators.

    Parameters
    ----------
    all_flat : list[KvnLine]
        All lines from the data segment, including KvLines, CommentLines, BlankLines.
    header_kws : set[str]
        Keywords belonging to the header section.
    meta_kws : set[str]
        Keywords belonging to the metadata section.

    Returns
    -------
    tuple[list[KvnLine], list[KvnLine], list[KvnLine]]
        (header_lines, meta_lines, data_lines)
    """
    n_flat = len(all_flat)

    # Pass 1: label KvLines
    flat_labels: list[str | None] = [None] * n_flat
    for i, ln in enumerate(all_flat):
        if isinstance(ln, KvLine):
            if ln.key in header_kws:
                flat_labels[i] = "header"
            elif ln.key in meta_kws:
                flat_labels[i] = "meta"
            else:
                flat_labels[i] = "data"

    # Pass 2: forward-looking for COMMENTs, orphans → "data"
    for i in range(n_flat):
        if flat_labels[i] is not None or isinstance(all_flat[i], BlankLine):
            continue
        has_blank = False
        next_label: str | None = None
        for j in range(i + 1, n_flat):
            if isinstance(all_flat[j], BlankLine):
                has_blank = True
            elif flat_labels[j] is not None:
                next_label = flat_labels[j]
                break
        if next_label is not None and not has_blank:
            flat_labels[i] = next_label
        else:
            flat_labels[i] = "data"  # orphan → data (Rule 3)

    # Rule 4: orphan COMMENTs above the first header keyword → header
    first_hdr_pos = next(
        (i for i, lb in enumerate(flat_labels) if lb == "header"), n_flat
    )
    for i in range(first_hdr_pos):
        if isinstance(all_flat[i], CommentLine) and flat_labels[i] == "data":
            flat_labels[i] = "header"

    # Collect partitions (keep BlankLines in "data" for separator info)
    hdr_lines: list[KvnLine] = []
    meta_lines: list[KvnLine] = []
    data_lines: list[KvnLine] = []
    for i, ln in enumerate(all_flat):
        lbl = flat_labels[i]
        if isinstance(ln, BlankLine):
            data_lines.append(ln)  # preserve as separators for nested
        elif lbl == "header":
            hdr_lines.append(ln)
        elif lbl == "meta":
            meta_lines.append(ln)
        else:
            data_lines.append(ln)

    return hdr_lines, meta_lines, data_lines


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_object(doc: KvnDocument) -> object:
    """
    Map a :class:`KvnDocument` onto the xsdata dataclass tree for the
    detected NDM type.

    Delegates scalar/unit coercion and leaf-dataclass construction to the
    :func:`~ccsds_ndm.kvn_utils.build_ndm_object` and
    :func:`~ccsds_ndm.kvn_utils.init_root_ndm_object` helpers from the
    legacy :mod:`ccsds_ndm.kvn_utils` module.

    Parameters
    ----------
    doc : KvnDocument
        Output of :func:`parse_blocks`.

    Returns
    -------
    object
        Fully populated root xsdata dataclass instance.
    """
    # Extract the root xsdata dataclass from the NDM type enum member.
    # This is the top-level class for the detected message type (e.g., Oem, Aem, etc.)
    clazz = doc.ndm_type.clazz  # type: ignore

    # ===================================================================
    # Inspect the root class structure to determine how segments are organized
    # ===================================================================
    # Resolve type hints to get the field types for header and body
    root_hints = _hints(clazz)
    header_field_type = _unwrap(root_hints["header"])
    body_field_type = _unwrap(root_hints["body"])
    body_hints = _hints(body_field_type)

    # Determine if segments are stored as a list (multi-segment types like OEM, AEM, TDM)
    # or as a single object (flat types like OPM, OMM, etc.)
    segment_field_type_raw = body_hints["segment"]
    is_multi_segment = getattr(segment_field_type_raw, "__origin__", None) is list
    if is_multi_segment:
        segment_clazz = _unwrap(segment_field_type_raw.__args__[0])
    else:
        segment_clazz = _unwrap(segment_field_type_raw)

    # Extract the segment structure: each segment has metadata and data fields
    seg_hints = _hints(segment_clazz)
    meta_clazz = _unwrap(seg_hints["metadata"])
    data_clazz = _unwrap(seg_hints["data"])

    # ===================================================================
    # Determine document type: flat or segment-based
    # ===================================================================
    # Flat types (OPM, OMM, APM, RDM, CDM) have no section markers, so their
    # first segment's metadata list is empty. Segment-based types (OEM, AEM, TDM)
    # always have metadata (between META_START and META_STOP markers).
    is_flat = bool(doc.segments) and not doc.segments[0].meta

    if is_flat:
        # Extract expected keywords for header and metadata from their class definitions
        header_kws = set(get_ccsds_kw_list(header_field_type)) - {"COMMENT"}
        meta_kws = set(get_ccsds_kw_list(meta_clazz)) - {"COMMENT"}

        # CDM (Conjunction Data Message) is a special flat type with a two-part structure:
        # relative_metadata_data and segment (containing relative and primary objects).
        # Other flat types have a simple structure: header + segment(metadata + data).
        if "relative_metadata_data" in body_hints:
            return _build_cdm_flat_object(
                doc,
                header_field_type,
                meta_clazz,
                data_clazz,
                body_field_type,
                segment_clazz,
                header_kws,
                meta_kws,
                clazz,
            )

        # --- Non-CDM flat types (OPM, OMM, APM, RDM) ---
        # Partition by keyword membership; COMMENTs use forward-looking
        # assignment; BlankLines are preserved in the data partition so
        # that _build_nested_data can use them as separators.
        all_flat = doc.segments[0].data
        hdr_from_data, meta_lines, data_lines = _partition_flat_type_lines(
            all_flat, header_kws, meta_kws
        )
        hdr_lines = list(doc.header) + hdr_from_data

        ndm_header = build_ndm_object(header_field_type, _kvlines_to_rows(hdr_lines))
        seg_meta = build_ndm_object(meta_clazz, _kvlines_to_rows(meta_lines))
        seg_data = _build_nested_data(data_clazz, data_lines)

        built_seg = _lenient_class_factory(
            segment_clazz, {"metadata": seg_meta, "data": seg_data}
        )
        ndm_body = _lenient_class_factory(body_field_type, {"segment": built_seg})
        return _lenient_class_factory(clazz, {"header": ndm_header, "body": ndm_body})

    # ===================================================================
    # Segment-based types (OEM, AEM, TDM)
    # ===================================================================
    # For segment-based types, there are explicit section markers (META_START,
    # META_STOP, DATA_START, DATA_STOP, COVARIANCE_START, COVARIANCE_STOP) that
    # separate metadata, data, and covariance blocks. Each block is processed
    # independently and assembled into a single segment.

    # Build the common header (present in all NDM types)
    header_rows = _kvlines_to_rows(doc.header)
    ndm_header = build_ndm_object(header_field_type, header_rows)

    built_segments: list[object] = []

    # Identify the specific segment type by checking for type-specific fields
    is_oem = _has_field(data_clazz, "state_vector") and is_multi_segment
    is_aem = _has_field(data_clazz, "attitude_state")
    is_tdm = _has_field(data_clazz, "observation")

    # OEM segments accumulate state vectors and can have separate covariance blocks
    oem_segments: list[tuple[object, object]] = []

    for block in doc.segments:
        # OEM covariance blocks are processed separately and attached to the
        # most recent state vector block. Skip if no state vectors yet.
        if block.covariance:
            if not oem_segments:
                continue
            cov_clazz = _unwrap(_hints(data_clazz)["covariance_matrix"].__args__[0])
            cov_fields = [
                f
                for f in dataclasses.fields(cov_clazz)
                if f.metadata.get("name", "").isupper()
                and f.metadata.get("name") not in ("COMMENT", "EPOCH", "COV_REF_FRAME")
            ]
            cov_hints = _hints(cov_clazz)

            # Split covariance lines into per-EPOCH groups
            cov_groups: list[list[KvnLine]] = []
            for ln in block.covariance:
                if isinstance(ln, KvLine) and ln.key == "EPOCH":
                    cov_groups.append([])
                if cov_groups:
                    cov_groups[-1].append(ln)

            for group in cov_groups:
                group_rows = _kvlines_to_rows(group)
                group_matrix_values = [
                    ln.tokens for ln in group if isinstance(ln, CovarianceRowLine)
                ]
                cov_obj = build_ndm_object(cov_clazz, group_rows)
                flat_vals = [v for row in group_matrix_values for v in row]
                for cf, val_str in zip(cov_fields, flat_vals):
                    cf_type = _unwrap(cov_hints[cf.name])
                    leaf_hints = _hints(cf_type)
                    leaf_val = float(val_str)
                    setattr(
                        cov_obj,
                        cf.name,
                        cf_type(**{list(leaf_hints.keys())[0]: leaf_val}),
                    )
                last_data = oem_segments[-1][1]
                last_data.covariance_matrix.append(cov_obj)
            continue

        meta_rows = _kvlines_to_rows(block.meta)
        data_rows = _kvlines_to_rows(block.data)

        if is_oem:
            seg_meta = build_ndm_object(meta_clazz, meta_rows)
            seg_data = init_root_ndm_object(data_clazz)
            for row in data_rows:
                if row[0] == "COMMENT":
                    seg_data.comment.append(row[1])
            sv_clazz = _unwrap(_hints(data_clazz)["state_vector"].__args__[0])
            sv_kws = [
                f.metadata.get("name")
                for f in dataclasses.fields(sv_clazz)
                if f.metadata.get("name") and f.metadata.get("name") != "COMMENT"
            ]
            for ln in block.data:
                if isinstance(ln, PackedDataLine):
                    sv_rows = [[kw, tok] for kw, tok in zip(sv_kws, ln.tokens)]
                    sv_obj = build_ndm_object(sv_clazz, sv_rows)
                    seg_data.state_vector.append(sv_obj)
            oem_segments.append((seg_meta, seg_data))

        elif is_aem:
            seg_meta = build_ndm_object(meta_clazz, meta_rows)
            seg_data = init_root_ndm_object(data_clazz)
            for row in data_rows:
                if row[0] == "COMMENT":
                    seg_data.comment.append(row[1])
            template = _att_column_template(block.meta)
            att_state_clazz = _unwrap(_hints(data_clazz)["attitude_state"].__args__[0])
            kv_meta = {ln.key: ln.value for ln in block.meta if isinstance(ln, KvLine)}
            att_type_str = kv_meta.get("ATTITUDE_TYPE", "").upper()
            _att_field_map = {
                "QUATERNION": "quaternion_state",
                "QUATERNION/DERIVATIVE": "quaternion_derivative",
                "QUATERNION/RATE": "quaternion_euler_rate",
                "EULER_ANGLE": "euler_angle",
                "EULER_ANGLE/RATE": "euler_angle_rate",
                "SPIN": "spin",
                "SPIN/NUTATION": "spin_nutation",
            }
            att_field_name = _att_field_map.get(att_type_str, "quaternion_state")
            att_sub_clazz_type = _hints(att_state_clazz)[att_field_name]
            att_sub_clazz = _unwrap(att_sub_clazz_type)

            for ln in block.data:
                if isinstance(ln, PackedDataLine):
                    packed_kvlines = [
                        KvLine(key=kw, value=tok)
                        for kw, tok in zip(template, ln.tokens)
                    ]
                    sub_obj = _build_sub_object(att_sub_clazz, packed_kvlines)
                    att_obj = _lenient_class_factory(
                        att_state_clazz, {att_field_name: sub_obj}
                    )
                    seg_data.attitude_state.append(att_obj)
            built_segments.append(
                _lenient_class_factory(
                    segment_clazz, {"metadata": seg_meta, "data": seg_data}
                )
            )

        elif is_tdm:
            seg_meta = build_ndm_object(meta_clazz, meta_rows)
            seg_data = init_root_ndm_object(data_clazz)
            for row in data_rows:
                if row[0] == "COMMENT":
                    seg_data.comment.append(row[1])
            obs_clazz = _unwrap(_hints(data_clazz)["observation"].__args__[0])
            for ln in block.data:
                if isinstance(ln, TdmObsLine):
                    obs_rows = [["EPOCH", ln.epoch], [ln.key, ln.value]]
                    obs_obj = build_ndm_object(obs_clazz, obs_rows)
                    seg_data.observation.append(obs_obj)
            built_segments.append(
                _lenient_class_factory(
                    segment_clazz, {"metadata": seg_meta, "data": seg_data}
                )
            )

    # Assemble OEM segments (with covariance already attached)
    if is_oem:
        for seg_meta, seg_data in oem_segments:
            built_segments.append(
                _lenient_class_factory(
                    segment_clazz, {"metadata": seg_meta, "data": seg_data}
                )
            )

    # -----------------------------------------------------------------------
    # Assemble the final NDM object
    # -----------------------------------------------------------------------
    # Create the body with either a list of segments (multi-segment types like OEM, AEM, TDM)
    # or a single segment (flat types like OPM, OMM when they reach here, though they exit earlier)
    if is_multi_segment:
        ndm_body = _lenient_class_factory(body_field_type, {"segment": built_segments})
    else:
        ndm_body = _lenient_class_factory(
            body_field_type, {"segment": built_segments[0] if built_segments else None}
        )

    # Create the root NDM object with header and body, completing the dataclass tree
    return _lenient_class_factory(clazz, {"header": ndm_header, "body": ndm_body})
