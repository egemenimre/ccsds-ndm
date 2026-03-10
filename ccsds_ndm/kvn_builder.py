# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
KVN object builder: mapping a :class:`~ccsds_ndm.kvn_parser.KvnDocument`
onto the xsdata dataclass tree for the detected NDM type.

Registry dispatch
-----------------
The ``build_object`` entry point uses the schema registry to decide which
structural variant (flat / segmented / CDM) to use, replacing the old
approach of probing the ``KvnDocument`` structure at runtime.

``_build_sub_object`` uses the registry's per-type handler sentinels to
dispatch to special builders (rotation types, etc.) instead of hard-coding
class names.
"""

from __future__ import annotations

import dataclasses
import enum
import types as _types
import typing
from collections.abc import Sequence

from ccsds_ndm.kvn_handlers import (
    DISPATCH_CDM,
    DISPATCH_SEGMENTED,
    PARSE_ROTATION_ANGLE,
    PARSE_ROTATION_RATE,
)
from ccsds_ndm.kvn_parser import KvnDocument
from ccsds_ndm.kvn_registry import VERSION_REGISTRY
from ccsds_ndm.kvn_tokenizer import (
    BlankLine,
    CommentLine,
    CovarianceRowLine,
    KvLine,
    KvnLine,
    PackedDataLine,
    TdmObsLine,
)

# ---------------------------------------------------------------------------
# Low-level utilities
# ---------------------------------------------------------------------------


def _unwrap(t) -> typing.Any:
    """Strip ``Optional[X]`` / ``None | X`` → ``X``; return *t* unchanged otherwise."""
    origin = getattr(t, "__origin__", None)
    # On Python 3.11-3.13, ``get_type_hints()`` resolves ``None | X`` (PEP 604
    # union syntax) to a ``types.UnionType`` which has no ``__origin__``.
    # On Python 3.14+ it resolves to ``typing.Union`` (origin is typing.Union).
    # We therefore check both the origin attribute and isinstance to cover all
    # supported versions.
    if origin is typing.Union or isinstance(t, _types.UnionType):
        args = [a for a in t.__args__ if a is not type(None)]
        return args[0] if args else str
    return t


def _coerce_value(raw_value, field_type):
    """
    Convert a raw KVN string value to the Python type expected by a dataclass field.

    Handles ``enum.Enum`` subclasses (looked up by value), ``float``, and
    ``int``.  Any other type is returned as-is (already a ``str``).
    ``Optional`` wrappers are stripped first.
    """
    base = _unwrap(field_type)
    if isinstance(base, type) and issubclass(base, enum.Enum):
        return base(raw_value)
    if base is float:
        return float(raw_value)
    if base is int:
        return int(raw_value)
    return raw_value


def _lenient_class_factory(clazz, params):
    """
    Instantiate ``clazz`` from ``params``, filling any missing required field with ``None``.
    """
    for f in dataclasses.fields(clazz):
        if f.init and f.name not in params:
            if (
                f.default is dataclasses.MISSING
                and f.default_factory is dataclasses.MISSING
            ):
                params[f.name] = None
    return clazz(**params)


def init_root_ndm_object(clazz):
    """
    Instantiate a root NDM class (e.g. ``Apm``, ``Oem``) with ``None`` placeholders.
    """
    init_kwargs = {
        f.name: None
        for f in dataclasses.fields(clazz)
        if f.init
        and f.default is dataclasses.MISSING
        and f.default_factory is dataclasses.MISSING
    }
    return clazz(**init_kwargs)


def get_ccsds_kw_list(clazz):
    """
    Returns the list of KVN keyword names recognised by ``clazz``.

    Handles dataclasses (field metadata ``"name"``), Enum types (member names),
    and edge classes (returns ``[]``).
    """
    if "__dataclass_fields__" in vars(clazz).keys():
        kw_list = [
            var.metadata["name"]
            for var in vars(clazz)["__dataclass_fields__"].values()
            if "name" in var.metadata.keys()
        ]
        return kw_list
    elif "_member_names_" in vars(clazz).keys():
        kw_list = [enum_tag for enum_tag in vars(clazz)["_member_names_"]]
        return kw_list
    else:
        return []


def build_ndm_object(clazz, local_lines, prefix=None):
    """
    Build a dataclass instance directly from KVN ``local_lines``.

    Each entry in ``local_lines`` is a list of 2 or 3 strings:
      ``[key, value]``           - plain field or nested single-value dataclass
      ``[key, value, units]``    - nested dataclass that also carries a units attribute
    """
    # Resolve forward-reference string annotations to actual type objects.
    # xsdata generates fields whose f.type is a plain string, not a type.
    resolved_hints = typing.get_type_hints(clazz)

    # Build a map from KVN keyword name → (field, resolved_type) for quick lookup.
    # The KVN keyword is stored in the dataclass field's metadata["name"].
    name_to_field = {
        f.metadata.get("name"): (f, resolved_hints[f.name])
        for f in dataclasses.fields(clazz)
        if f.name in resolved_hints
    }

    # This dictionary will hold the keyword arguments for instantiating `clazz`.
    params = {}

    # Handle the special case for USER_DEFINED parameters, which are prefixed.
    if prefix:
        # Find the dataclass field that corresponds to the prefix (e.g., "USER_DEFINED").
        entry = name_to_field.get(prefix)
        if entry is not None:
            list_field, list_type = entry
            # The field should be a list of a specific item type (e.g., UserDefinedParameterType).
            item_clazz = _unwrap(list_type.__args__[0])
            entries = []
            # Iterate over the KVN lines to find all user-defined parameters.
            for item in local_lines:
                if len(item) < 2 or not item[0].startswith(prefix + "_"):
                    continue
                param_name = item[0].replace(prefix + "_", "")
                entries.append(item_clazz(value=item[1], parameter=param_name))
            # Assign the list of user-defined parameters to the corresponding field.
            params[list_field.name] = entries
    else:
        # This is the general case for all other KVN key-value pairs.
        for item in local_lines:
            key, raw_val = item[0], item[1]
            # Find the dataclass field corresponding to the KVN key.
            entry = name_to_field.get(key)
            if entry is None:
                # If the key is not defined in the dataclass, ignore it.
                continue

            field, resolved_type = entry
            # Unwrap Optional[T] to get T.
            base_type = _unwrap(resolved_type)

            # Case 1: The field is a list (e.g., for multiple COMMENT lines).
            # xsdata marks list-like fields with a default_factory.
            if field.default_factory is not dataclasses.MISSING:
                # Get the type of items in the list.
                elem_type = _unwrap(base_type.__args__[0])
                # Append the coerced value to the list for this field.
                # setdefault ensures the list is created on first access.
                params.setdefault(field.name, []).append(
                    _coerce_value(raw_val, elem_type)
                )
            # Case 2: The field is a nested dataclass that represents a single value with units.
            elif dataclasses.is_dataclass(base_type):
                # These are "leaf" dataclasses like MomentType, with a 'value' and optional 'units'.
                leaf_hints = typing.get_type_hints(base_type)
                leaf_fields = dataclasses.fields(base_type)
                # The first field is assumed to be the main value.
                value_field = leaf_fields[0]
                leaf_params = {
                    value_field.name: _coerce_value(
                        raw_val, leaf_hints[value_field.name]
                    )
                }
                # If a unit is provided in the KVN line, find the 'units' attribute and set it.
                if len(item) > 2:
                    units_field = next(
                        (
                            f
                            for f in leaf_fields
                            if f.metadata.get("type") == "Attribute"
                        ),
                        None,
                    )
                    if units_field is not None:
                        leaf_params[units_field.name] = _coerce_value(
                            item[2], leaf_hints[units_field.name]
                        )
                # Instantiate the leaf dataclass and assign it to the parent's parameter dict.
                params[field.name] = typing.cast(typing.Callable, base_type)(
                    **leaf_params
                )
            else:
                # Case 3: The field is a simple scalar type (str, int, float, Enum).
                params[field.name] = _coerce_value(raw_val, resolved_type)

    # Instantiate the main dataclass. _lenient_class_factory fills missing
    # required fields with None, which is necessary because we build the object
    # piece by piece.
    return _lenient_class_factory(clazz, params)


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------

# Hard-coded keywords for RotationAngleType / RotationRateType
# (their fields have name=None, so get_ccsds_kw_list returns [])
_ROTATION_KWS: dict[str, list[str]] = {
    "RotationAngleType": ["X_ANGLE", "Y_ANGLE", "Z_ANGLE"],
    "RotationRateType": ["X_RATE", "Y_RATE", "Z_RATE"],
}

_AEM_FIELD_MAP: dict[str, str] = {
    "QUATERNION": "quaternion_state",
    "QUATERNION/DERIVATIVE": "quaternion_derivative",
    "QUATERNION/RATE": "quaternion_euler_rate",
    "EULER_ANGLE": "euler_angle",
    "EULER_ANGLE/RATE": "euler_angle_rate",
    "SPIN": "spin",
    "SPIN/NUTATION": "spin_nutation",
}


def _hints(clazz) -> dict:
    """Return the resolved type hints for *clazz*."""
    return typing.get_type_hints(clazz)


def _kvlines_to_rows(lines: Sequence[KvnLine]) -> list[list[str]]:
    """
    Convert a list of :class:`KvnLine` objects to the ``[key, value(, unit)]``
    row format expected by :func:`build_ndm_object`.
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


def _collect_all_kws(clazz) -> list[str]:
    """
    Return all KVN keywords reachable from *clazz*, recursing into
    no-``"name"`` sub-containers and camelCase container fields.
    """
    if clazz.__name__ in _ROTATION_KWS:
        return list(_ROTATION_KWS[clazz.__name__])
    kws = []
    hints = _hints(clazz)
    for f in dataclasses.fields(clazz):
        meta_name = f.metadata.get("name")
        if meta_name is None or meta_name == "":
            ftype = _unwrap(hints[f.name])
            if dataclasses.is_dataclass(ftype):
                kws.extend(_collect_all_kws(ftype))
        elif not meta_name.isupper():
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


def _build_rotation_type(rot_clazz, inst_lines: Sequence[KvnLine]) -> object:
    """Build a ``RotationAngleType`` or ``RotationRateType`` from ordered KvnLines."""
    rot_hints = _hints(rot_clazz)
    rot_fields = dataclasses.fields(rot_clazz)
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


def _att_column_template(meta_lines: Sequence[KvnLine]) -> list[str]:
    """
    Derive the packed-data column template for an AEM segment from its
    metadata lines.

    Returns a list of KVN keyword strings giving the column order, e.g.
    ``["EPOCH", "Q1", "Q2", "Q3", "QC"]``.
    """
    kv: dict[str, str] = {}
    for line in meta_lines:
        if isinstance(line, KvLine):
            kv[line.key] = line.value

    att_type = kv.get("ATTITUDE_TYPE", "")
    quat_type = kv.get("QUATERNION_TYPE", "FIRST").upper()
    rot_seq = kv.get("EULER_ROT_SEQ", "")

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

    # Fallback
    return ["EPOCH"]


def _forward_looking_pass(
    all_lines: Sequence[KvnLine],
    labels: list[str | None],
    fallback: str,
) -> list[str | None]:
    """
    Forward-looking pass: assign labels to unlabelled non-blank lines.

    Each unlabelled line looks ahead to the next labelled line.  If no blank
    line intervenes, it inherits that label; otherwise it falls back to
    *fallback*.  Mutates and returns *labels*.
    """
    n = len(all_lines)
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
            next_label if (next_label is not None and not has_blank) else fallback
        )
    return labels


def _label_lines(
    all_lines: Sequence[KvnLine],
    container_map: dict[str, tuple[str, type, bool]],
) -> list[str | None]:
    """
    Assign a label to every line in *all_lines*.

    Returns a parallel list of label strings (or ``None`` for BlankLines).
    Each label is either ``"own"`` or a field name string.
    """
    n = len(all_lines)
    labels: list[str | None] = [None] * n

    for i, ln in enumerate(all_lines):
        if isinstance(ln, KvLine):
            kw = ln.key
            if kw.startswith("USER_DEFINED_") or kw not in container_map:
                labels[i] = "own"
            else:
                labels[i] = container_map[kw][0]

    return _forward_looking_pass(all_lines, labels, "own")


def _partition_lines(
    all_lines: Sequence[KvnLine],
    labels: list[str | None],
    container_map: dict[str, tuple[str, type, bool]],
    list_first_kw: dict[str, str],
) -> tuple[list[KvnLine], dict[str, list[list[KvnLine]]]]:
    """
    Partition lines into "own" and per-container buckets using labels.
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

        assert lbl is not None
        fname = lbl
        if isinstance(ln, KvLine) and ln.key in container_map:
            _, _, is_list = container_map[ln.key]
            if is_list:
                first_kw = list_first_kw.get(fname)
                buckets = container_buckets.setdefault(fname, [])
                if ln.key == first_kw or not buckets:
                    stolen: list[KvnLine] = []
                    if buckets and buckets[-1]:
                        while buckets[-1] and isinstance(buckets[-1][-1], CommentLine):
                            stolen.append(buckets[-1].pop())
                        if not buckets[-1]:
                            buckets.pop()
                        stolen.reverse()
                    buckets.append(stolen + [ln])
                else:
                    buckets[-1].append(ln)
            else:
                buckets = container_buckets.setdefault(fname, [[]])
                buckets[-1].append(ln)
        else:
            buckets = container_buckets.setdefault(fname, [])
            if not buckets:
                buckets.append([ln])
            else:
                buckets[-1].append(ln)

    return own_lines, container_buckets


def _partition_flat_type_lines(
    all_flat: list[KvnLine], header_kws: set[str], meta_kws: set[str]
) -> tuple[list[KvnLine], list[KvnLine], list[KvnLine]]:
    """
    Partition flat-type document lines into header, metadata, and data sections.
    """
    n_flat = len(all_flat)

    flat_labels: list[str | None] = [None] * n_flat
    for i, ln in enumerate(all_flat):
        if isinstance(ln, KvLine):
            if ln.key in header_kws:
                flat_labels[i] = "header"
            elif ln.key in meta_kws:
                flat_labels[i] = "meta"
            else:
                flat_labels[i] = "data"

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
            flat_labels[i] = "data"

    # Rule 4: orphan COMMENTs above the first header keyword → header
    # (only applies when header keywords exist in the partition)
    first_hdr_pos = next(
        (i for i, lb in enumerate(flat_labels) if lb == "header"), None
    )
    if first_hdr_pos is not None:
        for i in range(first_hdr_pos):
            if isinstance(all_flat[i], CommentLine) and flat_labels[i] == "data":
                flat_labels[i] = "header"

    hdr_lines: list[KvnLine] = []
    meta_lines: list[KvnLine] = []
    data_lines: list[KvnLine] = []
    for i, ln in enumerate(all_flat):
        lbl = flat_labels[i]
        if isinstance(ln, BlankLine):
            data_lines.append(ln)
        elif lbl == "header":
            hdr_lines.append(ln)
        elif lbl == "meta":
            meta_lines.append(ln)
        else:
            data_lines.append(ln)

    return hdr_lines, meta_lines, data_lines


# ---------------------------------------------------------------------------
# Core recursive builders (adapted for registry dispatch)
# ---------------------------------------------------------------------------


def _build_sub_object(sub_clazz, inst_lines: Sequence[KvnLine], schema_reg) -> object:
    """
    Build a sub-container xsdata object from a flat list of KvnLines.

    Uses the registry to dispatch to special builders (rotation types, etc.)
    instead of hard-coding class names.
    """
    handler = schema_reg.get_handler(sub_clazz.__name__)

    if handler.parse in (PARSE_ROTATION_ANGLE, PARSE_ROTATION_RATE):
        return _build_rotation_type(sub_clazz, inst_lines)

    # PARSE_DEFAULT path
    has_nested = any(
        f.metadata.get("name", "") and not f.metadata["name"].isupper()
        for f in dataclasses.fields(sub_clazz)
    )
    if has_nested:
        return _build_nested_data(sub_clazz, inst_lines, schema_reg)

    # Standard: all UPPER_CASE keywords
    rows = _kvlines_to_rows(inst_lines)
    obj = build_ndm_object(sub_clazz, rows)

    # Handle no-"name" transparent sub-sub-containers
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


def _build_nested_data(data_cls, all_lines: Sequence[KvnLine], schema_reg) -> object:
    """
    Build a data object whose fields include camelCase sub-containers.

    Partitions flat KvnLines into per-container buckets by keyword membership,
    builds each sub-container with :func:`build_ndm_object` or a specialised
    builder, and attaches the results to the data object.
    """
    data_hints_local = _hints(data_cls)

    # --- Step 1: Build keyword → (field_name, sub_clazz, is_list) map ---
    container_map: dict[str, tuple[str, type, bool]] = {}
    list_first_kw: dict[str, str] = {}

    for f in dataclasses.fields(data_cls):
        meta_name = f.metadata.get("name", "")
        if not meta_name or meta_name.isupper():
            continue

        ftype_raw = data_hints_local[f.name]
        is_list_field = getattr(ftype_raw, "__origin__", None) is list
        if is_list_field:
            item_type = _unwrap(ftype_raw.__args__[0])
            kws = _collect_all_kws(item_type)
            for kw in kws:
                if kw and kw != "COMMENT":
                    container_map[kw] = (f.name, item_type, True)
            first = next((k for k in kws if k and k != "COMMENT"), None)
            if first:
                list_first_kw[f.name] = first
        else:
            sub_clazz = _unwrap(ftype_raw)
            kws = _collect_all_kws(sub_clazz)
            for kw in kws:
                if kw and kw != "COMMENT":
                    container_map[kw] = (f.name, sub_clazz, False)

    # --- Step 2: Label lines ---
    labels = _label_lines(all_lines, container_map)

    # --- Step 3: Partition lines ---
    own_lines, container_buckets = _partition_lines(
        all_lines, labels, container_map, list_first_kw
    )

    # --- Step 4: Build data object from own_rows ---
    own_rows = _kvlines_to_rows(own_lines)
    seg_data = build_ndm_object(data_cls, own_rows)

    # --- Step 5: Handle no-"name" sub-containers ---
    for f in dataclasses.fields(data_cls):
        meta_name = f.metadata.get("name")
        if (meta_name is None or meta_name == "") and dataclasses.is_dataclass(
            _unwrap(data_hints_local[f.name])
        ):
            inner_clazz = _unwrap(data_hints_local[f.name])
            inner_obj = build_ndm_object(inner_clazz, own_rows)
            setattr(seg_data, f.name, inner_obj)

    # --- Step 6: Build and attach each camelCase sub-container ---
    for f in dataclasses.fields(data_cls):
        meta_name = f.metadata.get("name", "")
        if not meta_name or meta_name.isupper():
            continue
        if f.name not in container_buckets:
            continue

        ftype_raw = data_hints_local[f.name]
        is_list_field = getattr(ftype_raw, "__origin__", None) is list
        buckets = container_buckets[f.name]

        if is_list_field:
            item_type = _unwrap(ftype_raw.__args__[0])
            built_list = [
                _build_sub_object(item_type, inst, schema_reg) for inst in buckets
            ]
            setattr(seg_data, f.name, built_list)
        else:
            sub_clazz = _unwrap(ftype_raw)
            inst = buckets[0] if buckets else []
            setattr(seg_data, f.name, _build_sub_object(sub_clazz, inst, schema_reg))

    # --- Step 7: USER_DEFINED parameters ---
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


# ---------------------------------------------------------------------------
# Flat-type builder (OPM, OMM, APM, RDM)
# ---------------------------------------------------------------------------


def _build_flat(
    doc: KvnDocument,
    root_clazz,
    header_clazz,
    body_clazz,
    segment_clazz,
    meta_clazz,
    data_clazz,
    schema_reg,
) -> object:
    """Build a flat-type (OPM, OMM, APM, RDM) NDM object."""
    header_kws = set(get_ccsds_kw_list(header_clazz)) - {"COMMENT"}
    meta_kws = set(get_ccsds_kw_list(meta_clazz)) - {"COMMENT"}

    all_flat = doc.segments[0].data
    hdr_from_data, meta_lines, data_lines = _partition_flat_type_lines(
        all_flat, header_kws, meta_kws
    )
    hdr_lines = list(doc.header) + hdr_from_data

    ndm_header = build_ndm_object(header_clazz, _kvlines_to_rows(hdr_lines))
    seg_meta = build_ndm_object(meta_clazz, _kvlines_to_rows(meta_lines))
    seg_data = _build_nested_data(data_clazz, data_lines, schema_reg)

    built_seg = _lenient_class_factory(
        segment_clazz, {"metadata": seg_meta, "data": seg_data}
    )
    ndm_body = _lenient_class_factory(body_clazz, {"segment": built_seg})
    return _lenient_class_factory(root_clazz, {"header": ndm_header, "body": ndm_body})


# ---------------------------------------------------------------------------
# CDM builder
# ---------------------------------------------------------------------------


def _label_cdm_lines(
    all_lines: list[KvnLine], header_kws: set[str]
) -> list[str | None]:
    """Label CDM data lines as "header" or "other"."""
    n = len(all_lines)
    labels: list[str | None] = [None] * n

    for i, ln in enumerate(all_lines):
        if isinstance(ln, KvLine):
            labels[i] = "header" if ln.key in header_kws else "other"

    _forward_looking_pass(all_lines, labels, "other")

    # Rule 4: orphan COMMENTs above first header keyword → header
    first_hdr = next((i for i, lb in enumerate(labels) if lb == "header"), n)
    for i in range(first_hdr):
        if isinstance(all_lines[i], CommentLine) and labels[i] == "other":
            labels[i] = "header"

    return labels


def _split_cdm_objects(
    all_lines: list[KvnLine], labels: list[str | None], doc_header: list[KvnLine]
) -> tuple[list[KvnLine], list[KvnLine], list[list[KvnLine]]]:
    """Split CDM data lines into header, relative metadata, and object segments."""
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
    schema_reg,
) -> object:
    """Build a single CDM object segment from a list of lines."""
    obj_n = len(obj_lines)
    obj_labels: list[str | None] = [None] * obj_n

    for idx, ln in enumerate(obj_lines):
        if isinstance(ln, KvLine):
            obj_labels[idx] = "meta" if ln.key in meta_kws else "data"

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

    obj_meta_lines: list[KvnLine] = []
    obj_data_lines: list[KvnLine] = []
    for idx, ln in enumerate(obj_lines):
        if isinstance(ln, BlankLine):
            obj_data_lines.append(ln)
        elif obj_labels[idx] == "meta":
            obj_meta_lines.append(ln)
        else:
            obj_data_lines.append(ln)

    seg_meta = build_ndm_object(meta_clazz, _kvlines_to_rows(obj_meta_lines))
    seg_data = _build_nested_data(data_clazz, obj_data_lines, schema_reg)
    return _lenient_class_factory(
        segment_clazz, {"metadata": seg_meta, "data": seg_data}
    )


def _build_cdm_flat_object(
    doc: KvnDocument,
    header_clazz,
    meta_clazz,
    data_clazz,
    body_clazz,
    segment_clazz,
    schema_reg,
    root_clazz,
) -> object:
    """
    Build a CDM (Conjunction Data Message) object.

    The new ``_dispatch_cdm`` in ``kvn_parser.py`` already splits the document
    into pre-structured segments:
    - ``doc.header``       — top-level header lines
    - ``doc.segments[0].meta`` — relative metadata lines
    - ``doc.segments[1].data`` — OBJECT 1 lines
    - ``doc.segments[2].data`` — OBJECT 2 lines
    """
    meta_kws = set(get_ccsds_kw_list(meta_clazz)) - {"COMMENT"}
    rel_meta_clazz = _unwrap(_hints(body_clazz)["relative_metadata_data"])

    # Build header
    ndm_header = build_ndm_object(header_clazz, _kvlines_to_rows(doc.header))

    # Build relative metadata from pre-split segment
    rel_meta_obj = _build_nested_data(rel_meta_clazz, doc.segments[0].meta, schema_reg)

    # Build object segments from pre-split segments
    built_segments = [
        _build_cdm_object_segment(
            seg.data, meta_kws, meta_clazz, data_clazz, segment_clazz, schema_reg
        )
        for seg in doc.segments[1:]
    ]

    ndm_body = _lenient_class_factory(
        body_clazz,
        {
            "relative_metadata_data": rel_meta_obj,
            "segment": built_segments,
        },
    )
    return _lenient_class_factory(root_clazz, {"header": ndm_header, "body": ndm_body})


# ---------------------------------------------------------------------------
# Segment-based builders (OEM, AEM, TDM)
# ---------------------------------------------------------------------------


def _init_segment(segment, meta_clazz, data_clazz) -> tuple[object, typing.Any]:
    """Build the common seg_meta and seg_data objects for a single segment."""
    meta_rows = _kvlines_to_rows(segment.meta)
    data_rows = _kvlines_to_rows(segment.data)
    seg_meta = build_ndm_object(meta_clazz, meta_rows)
    seg_data = init_root_ndm_object(data_clazz)
    for row in data_rows:
        if row[0] == "COMMENT":
            seg_data.comment.append(row[1])
    return seg_meta, seg_data


def _attach_oem_covariance(
    block_covariance: list[KvnLine],
    data_clazz,
    oem_segments: list[tuple[typing.Any, typing.Any]],
) -> None:
    """
    Build covariance matrix objects from a covariance block and attach them
    to the most recent OEM state-vector segment.
    """
    cov_clazz = _unwrap(_hints(data_clazz)["covariance_matrix"].__args__[0])
    cov_fields = [
        f
        for f in dataclasses.fields(cov_clazz)
        if f.metadata.get("name", "").isupper()
        and f.metadata.get("name") not in ("COMMENT", "EPOCH", "COV_REF_FRAME")
    ]
    cov_hints = _hints(cov_clazz)

    cov_groups: list[list[KvnLine]] = []
    for ln in block_covariance:
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


def _build_oem_segments(
    doc: KvnDocument,
    meta_clazz,
    data_clazz,
    segment_clazz,
    schema_reg=None,
) -> list[object]:
    """Build segments for OEM (Orbit Ephemeris Message) documents."""
    oem_segments: list[tuple[typing.Any, typing.Any]] = []

    for segment in doc.segments:
        if segment.covariance:
            if not oem_segments:
                continue
            _attach_oem_covariance(segment.covariance, data_clazz, oem_segments)
            continue

        seg_meta, seg_data = _init_segment(segment, meta_clazz, data_clazz)

        sv_clazz = _unwrap(_hints(data_clazz)["state_vector"].__args__[0])
        sv_kws = [
            f.metadata.get("name")
            for f in dataclasses.fields(sv_clazz)
            if f.metadata.get("name") and f.metadata.get("name") != "COMMENT"
        ]
        for ln in segment.data:
            if isinstance(ln, PackedDataLine):
                sv_rows = [[kw, tok] for kw, tok in zip(sv_kws, ln.tokens)]
                seg_data.state_vector.append(build_ndm_object(sv_clazz, sv_rows))

        oem_segments.append((seg_meta, seg_data))

    return [
        _lenient_class_factory(segment_clazz, {"metadata": m, "data": d})
        for m, d in oem_segments
    ]


def _build_aem_segments(
    doc: KvnDocument,
    meta_clazz,
    data_clazz,
    segment_clazz,
    schema_reg=None,
) -> list[object]:
    """Build segments for AEM (Attitude Ephemeris Message) documents."""
    built_segments: list[object] = []
    att_state_clazz = _unwrap(_hints(data_clazz)["attitude_state"].__args__[0])

    for segment in doc.segments:
        seg_meta, seg_data = _init_segment(segment, meta_clazz, data_clazz)

        template = _att_column_template(segment.meta)
        kv_meta = {ln.key: ln.value for ln in segment.meta if isinstance(ln, KvLine)}
        att_type_str = kv_meta.get("ATTITUDE_TYPE", "").upper()
        att_field_name = _AEM_FIELD_MAP.get(att_type_str, "quaternion_state")
        att_sub_clazz = _unwrap(_hints(att_state_clazz)[att_field_name])

        for ln in segment.data:
            if isinstance(ln, PackedDataLine):
                packed_kvlines = [
                    KvLine(key=kw, value=tok) for kw, tok in zip(template, ln.tokens)
                ]
                sub_obj = _build_sub_object(att_sub_clazz, packed_kvlines, schema_reg)
                att_obj = _lenient_class_factory(
                    att_state_clazz, {att_field_name: sub_obj}
                )
                seg_data.attitude_state.append(att_obj)

        built_segments.append(
            _lenient_class_factory(
                segment_clazz, {"metadata": seg_meta, "data": seg_data}
            )
        )

    return built_segments


def _build_tdm_segments(
    doc: KvnDocument,
    meta_clazz,
    data_clazz,
    segment_clazz,
    schema_reg=None,
) -> list[object]:
    """Build segments for TDM (Tracking Data Message) documents."""
    built_segments: list[object] = []
    obs_clazz = _unwrap(_hints(data_clazz)["observation"].__args__[0])

    for segment in doc.segments:
        seg_meta, seg_data = _init_segment(segment, meta_clazz, data_clazz)

        for ln in segment.data:
            if isinstance(ln, TdmObsLine):
                obs_rows = [["EPOCH", ln.epoch], [ln.key, ln.value]]
                seg_data.observation.append(build_ndm_object(obs_clazz, obs_rows))

        built_segments.append(
            _lenient_class_factory(
                segment_clazz, {"metadata": seg_meta, "data": seg_data}
            )
        )

    return built_segments


# Dispatch table: data class name → segment builder function
_SEGMENT_BUILDERS: dict[str, typing.Callable] = {
    "OemData": _build_oem_segments,
    "AemData": _build_aem_segments,
    "TdmData": _build_tdm_segments,
}


def _build_segment_based_object(
    doc: KvnDocument,
    header_clazz,
    meta_clazz,
    data_clazz,
    segment_clazz,
    schema_reg=None,
) -> tuple[object, list[object]]:
    """Build header and segments for segment-based types (OEM, AEM, TDM)."""
    header_rows = _kvlines_to_rows(doc.header)
    ndm_header = build_ndm_object(header_clazz, header_rows)

    builder = _SEGMENT_BUILDERS[data_clazz.__name__]
    built_segments = builder(doc, meta_clazz, data_clazz, segment_clazz, schema_reg)

    return ndm_header, built_segments


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_object(doc: KvnDocument) -> object:
    """
    Map a :class:`KvnDocument` onto the xsdata dataclass tree for the
    detected NDM type.

    Uses the schema registry to determine the document dispatch strategy
    (flat / segmented / CDM) instead of probing the document structure.

    Parameters
    ----------
    doc : KvnDocument
        Output of :func:`~ccsds_ndm.kvn_parser.dispatch_document`.

    Returns
    -------
    object
        Fully populated root xsdata dataclass instance.
    """
    root_clazz = doc.ndm_type.clazz
    schema_reg = VERSION_REGISTRY[doc.ndm_type.req_combi_version]

    # Resolve the type chain
    root_hints = _hints(root_clazz)
    header_clazz = _unwrap(root_hints["header"])
    body_clazz = _unwrap(root_hints["body"])
    body_hints = _hints(body_clazz)

    segment_field_type_raw = body_hints["segment"]
    is_list_segment = getattr(segment_field_type_raw, "__origin__", None) is list
    if is_list_segment:
        segment_clazz = _unwrap(segment_field_type_raw.__args__[0])
    else:
        segment_clazz = _unwrap(segment_field_type_raw)

    seg_hints = _hints(segment_clazz)
    meta_clazz = _unwrap(seg_hints["metadata"])
    data_clazz = _unwrap(seg_hints["data"])

    # Use registry dispatch sentinel
    dispatch = schema_reg.dispatch.get(root_clazz.__name__)

    if dispatch == DISPATCH_CDM:
        return _build_cdm_flat_object(
            doc,
            header_clazz,
            meta_clazz,
            data_clazz,
            body_clazz,
            segment_clazz,
            schema_reg,
            root_clazz,
        )
    elif dispatch == DISPATCH_SEGMENTED:
        ndm_header, built_segments = _build_segment_based_object(
            doc, header_clazz, meta_clazz, data_clazz, segment_clazz, schema_reg
        )
        ndm_body = _lenient_class_factory(body_clazz, {"segment": built_segments})
        return _lenient_class_factory(
            root_clazz, {"header": ndm_header, "body": ndm_body}
        )
    else:  # DISPATCH_FLAT
        return _build_flat(
            doc,
            root_clazz,
            header_clazz,
            body_clazz,
            segment_clazz,
            meta_clazz,
            data_clazz,
            schema_reg,
        )
