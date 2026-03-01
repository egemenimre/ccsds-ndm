# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Utilities for the KVN File I/O.

"""
import dataclasses
import enum
import importlib
import inspect
import types
import typing
from collections import namedtuple
from dataclasses import Field

from ccsds_ndm.mapping import _NdmDataType

_MinMaxTuple = namedtuple("_MinMaxTuple", ["min", "max"])
"""Data structure to keep min and max index bounds (both inclusive start, exclusive end)."""


def identify_data_type(kvn_source: list[list]) -> _NdmDataType:
    """
    Identify the NDM data type from a parsed KVN source.

    Reads the ``CCSDS_*_VERS`` keyword from the first two rows of the parsed
    KVN source (the first row contains the keyword name such as
    ``"CCSDS_OMM_VERS"``, the second contains the version number) and
    delegates to ``_NdmDataType.find_ndm_type_by_class_id`` to map them to
    the correct model class.

    Parameters
    ----------
    kvn_source : list[list]
        Parsed KVN data as a list of rows, where each row is a list of
        strings ``[key, value, ...]``. The ``CCSDS_*_VERS`` keyword is
        expected in ``kvn_source[0][1]`` and the version string in
        ``kvn_source[1][1]``.

    Returns
    -------
    _NdmDataType
        The identified NDM data type descriptor.

    """
    # id and version guaranteed to be in the first and the second rows.
    id_str = kvn_source[0][1]
    version_str = kvn_source[1][1]

    return _NdmDataType.find_ndm_type_by_class_id(id_str, version_str)


def is_id_or_version(name: str):
    """
    Returns ``True`` if ``name`` is the reserved field name ``"id"`` or ``"version"``.

    These two fields are populated from the ``CCSDS_*_VERS`` header line and
    must not be mapped from regular KVN key/value pairs during parsing.
    """
    if name == "id" or name == "version":
        return True
    else:
        return False


def is_list(field_data: Field):
    """
    Returns ``True`` if the dataclass field holds a list value.

    Checks whether ``field_data.default_factory`` is ``list``, which is how
    xsdata marks repeatable (0..N) fields such as COMMENT lines or
    multi-segment data blocks.
    """
    if field_data.default_factory and field_data.default_factory is list:
        return True
    else:
        return False


def is_class(field_data: Field):
    """
    Returns ``True`` if the dataclass field represents a nested NDM class.

    In the xsdata-generated models, every field carries a ``"name"`` metadata
    key.  Fields whose name is all-uppercase are KVN keyword tags (leaf values
    such as ``"EPOCH"`` or ``"MASS"``); mixed-case names are nested class
    fields (such as ``"header"`` or ``"metaData"``).  Fields with no ``"name"``
    metadata at all are also treated as nested classes.
    """
    if "name" in field_data.metadata.keys():
        # can be a tag or low level class
        if field_data.metadata["name"].isupper():
            return False
        else:
            return True
    return True


def get_ccsds_kw_list(clazz):
    """
    Returns the list of KVN keyword names recognised by ``clazz``.

    Handles three kinds of classes:

    * **Dataclasses** — extracts the ``"name"`` metadata value from each
      field that has one. These are the KVN keyword strings (e.g.
      ``"EPOCH"``, ``"MASS"``).
    * **Enum types** — returns the enum member names directly (used when a
      field is constrained to a fixed set of string values).
    * **Edge classes** (e.g. ``Decimal``, ``str``) — returns an empty list
      because these types carry no keyword metadata.
    """
    if "__dataclass_fields__" in vars(clazz).keys():
        kw_list = [
            var.metadata["name"]
            for var in vars(clazz)["__dataclass_fields__"].values()
            if "name" in var.metadata.keys()
        ]

        # print(kw_list)

        return kw_list
    elif "_member_names_" in vars(clazz).keys():
        # This is an enumerator type
        kw_list = [enum_tag for enum_tag in vars(clazz)["_member_names_"]]

        return kw_list
    else:
        # This is probably an "edge class" like Decimal
        return []


def _split_into_segments(block: list[tuple]) -> list[list[tuple]]:
    """
    Splits a flat list of (idx, key) pairs into segments.

    Blank lines (key == "") act as primary segment separators. Within each
    blank-line-delimited run, any leading COMMENT entries are split into their
    own separate segment so that ``_is_comment_seg`` can correctly classify
    them as comment-only (not mixed with data). Returns a list of non-empty
    segments.
    """
    segments = []
    current = []

    def _flush(run):
        """Split a non-blank run at the first non-COMMENT entry."""
        if not run:
            return
        # Find where the leading COMMENTs end
        split_at = next(
            (i for i, (_, k) in enumerate(run) if k != "COMMENT"), len(run)
        )
        if 0 < split_at < len(run):
            # Mixed: leading comments + data — emit as two separate segments
            segments.append(run[:split_at])
            segments.append(run[split_at:])
        else:
            segments.append(run)

    for idx, key in block:
        if key == "":
            _flush(current)
            current = []
        else:
            current.append((idx, key))
    _flush(current)
    return segments


def _is_comment_seg(seg: list[tuple]) -> bool:
    """Returns True if every entry in the segment is a COMMENT."""
    return all(k == "COMMENT" for _, k in seg)


def process_comment_lines(
    tags: list,
    start_index: int,
    keys: list,
    index_list: list,
) -> None:
    """
    Claim COMMENT line indexes and append them to ``index_list``.

    Algorithm
    ---------
    1. If ``"COMMENT"`` is not in ``tags``, do nothing.
    2. If ``tags`` has exactly one entry (a container class like AemData), claim
       at most one COMMENT at ``start_index``.
    3. Otherwise scan forward from ``start_index`` until a key that is neither
       in ``tags``, ``"COMMENT"``, nor ``""`` (blank line) is found (a *foreign key*).
       The span is split into blank-line-delimited segments and classified as:

       * **Leading** (before first data segment) — always claimed.
       * **Trailing** (after last data segment):

         - If the scan was stopped by a foreign key, any comment-only segment
           immediately before that key belongs to the *next* block — do not claim it.
         - If the scan reached end-of-file (no foreign key), there is no next block,
           (likely end-of file) so all trailing comments are claimed.

    Parameters
    ----------
    tags : list
        All keyword tags recognised by this block.
    start_index : int
        Index in ``keys`` where the block begins.
    keys : list
        Full list of KVN keys (including ``""`` for blank lines).
    index_list : list
        Accumulator; matched line indexes are appended here.
    """
    if "COMMENT" not in tags:
        return

    if len(tags) == 1:
        # Single-tag (container) class such as AemData, OemData, or CdmData: it holds
        # only COMMENT children directly.
        #
        # Claim consecutive COMMENTs starting from start_index (skipping leading blanks).
        # Stop before the first COMMENT that is immediately followed (without any
        # intervening blank line) by a non-COMMENT, non-blank key — that COMMENT belongs
        # to a child block that owns those keys.
        # Example: "COMMENT A\nCOMMENT B\nTIME_LASTOB_START" → only claim A.
        # Example: "COMMENT A\nCOMMENT B\n\nEPOCH_DATA" → claim both A and B.
        pending: list[int] = []  # COMMENTs in current blank-free run
        for idx in range(start_index, len(keys)):
            key = keys[idx]
            if key == "":
                # Blank line: flush pending COMMENTs (they're separated from next block)
                index_list.extend(pending)
                pending = []
            elif key == "COMMENT":
                pending.append(idx)
            else:
                # Real key immediately adjacent to pending COMMENTs → they belong to
                # the child that owns this key; do not claim them.
                pending = []
                break
        # Remaining pending at EOF (loop exhausted without hitting a real key) → claim
        index_list.extend(pending)
        return

    # --- Step 1: collect the block ---
    # Scan forward from start_index and gather every (idx, key) pair that belongs
    # to this block. A key belongs when it is a recognised tag, a COMMENT, or a
    # blank line (""). Stop as soon as a key that is none of these is encountered
    # (it belongs to the next block). Record whether we were stopped by a foreign key
    # or simply ran off the end of the file.
    block = []
    hit_foreign = False
    for idx in range(start_index, len(keys)):
        key = keys[idx]
        if key == "" or key in tags or key == "COMMENT":
            block.append((idx, key))
        else:
            hit_foreign = True
            break

    # --- Step 2: split on blank lines ---
    # Blank lines act as visual separators in KVN files. Partition the block into
    # contiguous non-blank runs ("segments"). Each segment is either a data segment
    # (contains at least one non-COMMENT key) or a comment-only segment.
    segments = _split_into_segments(block)
    if not segments:
        return

    # --- Step 3: locate data boundaries ---
    # Find the first and last segments that contain actual data keys (not just COMMENTs).
    # These anchor points determine which comment segments are "leading" vs "trailing".
    first_data = next(
        (i for i, s in enumerate(segments) if not _is_comment_seg(s)), None
    )
    last_data = next(
        (
            i
            for i in range(len(segments) - 1, -1, -1)
            if not _is_comment_seg(segments[i])
        ),
        None,
    )

    if first_data is None:
        # No data segments at all — every segment is comment-only.
        # If the scan was stopped by a foreign key, these comments introduce that
        # next block, so do not claim any of them.
        # If we reached EOF, claim all (no next block exists).
        if not hit_foreign:
            for seg in segments:
                for idx, key in seg:
                    if key == "COMMENT":
                        index_list.append(idx)
        return

    # --- Step 4: decide which segments to claim ---
    # All leading segments (before the first data segment) are always claimed,
    # regardless of whether they are adjacent to the data or separated by blank lines.
    claim = set(range(0, first_data))

    # Trailing segments (after the last data segment): the last comment-only segment
    # in the block is immediately adjacent to the foreign key that ended the scan, so
    # it belongs to the *next* block — exclude it. If we reached EOF instead, there
    # is no next block, so claim all trailing segments.
    assert (
        last_data is not None
    )  # guaranteed: first_data is not None implies last_data is not None
    trailing_start = last_data + 1
    trailing_end = len(segments)  # exclusive

    if hit_foreign:
        # All trailing comment-only segments after the last data segment belong to the
        # next block (COMMENTs always introduce the block that follows them).
        # Do not claim any of them.
        pass
    else:
        # Reached end of file — no next block, so claim all trailing comment segments.
        for i in range(trailing_start, trailing_end):
            if _is_comment_seg(segments[i]):
                claim.add(i)

    # --- Step 5: emit claimed COMMENT indexes ---
    for seg_idx in sorted(claim):
        for idx, key in segments[seg_idx]:
            if key == "COMMENT":
                index_list.append(idx)


def get_index(key: str, keys: list, *args) -> int | None:
    """
    Returns the first index of ``key`` in ``keys``, or ``None`` if not found.

    Parameters
    ----------
    key : str
        Key value to search for (e.g. ``"CREATION_DATE"``).
    keys : list[str]
        List of KVN keys.
    args
        Optional extra arguments forwarded to ``list.index`` (e.g. a start index).
    """
    try:
        return keys.index(key, *args)
    except ValueError:
        return None


def get_min_max_indices(
    tags: list, start_index: int, keys: list, prefix=None, single_elem=None
) -> _MinMaxTuple:
    """
    Returns the min/max index bounds of a KVN block.

    Matches ``tags`` against ``keys`` from ``start_index`` onward and returns
    a ``_MinMaxTuple`` spanning the first and last matched positions.

    Parameters
    ----------
    tags : list[str]
        All keyword tags recognised by this block (may include ``"COMMENT"``).
    start_index : int
        Position in ``keys`` where the search begins.
    keys : list[str]
        Full list of KVN keys.
    prefix : str or None
        If given, any key in ``keys`` starting with this prefix is added to ``tags``
        dynamically (used for ``USER_DEFINED`` fields).
    single_elem : str or None
        If truthy, only the first matched tag position is returned (width = 1).
    """
    if prefix:
        new_keys = [key for key in keys[start_index:] if key.startswith(prefix)]
        tags.extend(new_keys)

    # Find the index of each recognised tag, skipping COMMENTs (handled separately)
    index_named_list = [
        [tag, get_index(tag, keys, start_index)] for tag in tags if tag != "COMMENT"
    ]

    # Drop tags that were not found in this region
    index_list = [idx for _, idx in index_named_list if idx is not None]

    # Claim COMMENT lines that belong to this block
    process_comment_lines(tags, start_index, keys, index_list)

    # Check for non-consecutive data and chop if necessary.
    # Gaps can mean a nested sub-block or inline numeric data separated by spaces.
    if index_list:
        index_list.sort()
        ideal_list = list(range(min(index_list), max(index_list) + 1))
        diff_list = [n for n in ideal_list if n not in index_list]

        if diff_list:
            containing_spaces = any(" " in keys[n] for n in diff_list)

            # Detect repeating keys in the gap (ignore blank lines and comments)
            diff_keys = [keys[i] for i in diff_list if keys[i] not in ("", "COMMENT")]
            repeating_data = len(diff_keys) != len(set(diff_keys))

            if containing_spaces or repeating_data:
                # Gap is inline numeric data — chop to the consecutive prefix only
                index_list = [
                    n
                    for i, n in enumerate(index_list)
                    if index_list[i] == ideal_list[i]
                ]

    if not index_list:
        return _MinMaxTuple(start_index, start_index)

    min_of_list = min(index_list)
    if single_elem:
        max_of_list = min_of_list + 1
    else:
        max_of_list = max(index_list) + 1  # exclusive upper bound
    return _MinMaxTuple(min_of_list, max_of_list)


def _is_date_str(s: str) -> bool:
    """
    Returns ``True`` if ``s`` looks like a KVN epoch string.

    A KVN epoch starts with a 4-digit year followed by ``"-"``, e.g.
    ``"2007-075T16:50:01"`` (day-of-year form) or ``"2020-12-29T06:26:10"``
    (calendar form).
    """
    return len(s) >= 5 and s[:4].isnumeric() and s[4] == "-"


def _first_non_blank(lines: list, init_index: int, col: int) -> tuple:
    """
    Returns ``(index, value)`` for the first non-empty cell in column ``col``.

    Scans ``lines`` from ``init_index`` onward and returns the row index and
    value of the first row where ``lines[i][col]`` is non-empty (i.e. the row
    has enough columns and the cell is a non-empty string). Blank/short rows
    are skipped silently.

    Returns ``(init_index, "")`` if no matching row is found before the end of
    the list (e.g. end of file).

    Parameters
    ----------
    lines : list
        Full KVN line list; each entry is a list of string tokens.
    init_index : int
        Row index to start scanning from (inclusive).
    col : int
        Column index to inspect — ``0`` for the key column, ``1`` for the
        value column.
    """
    return next(
        (
            (i, lines[i][col])
            for i in range(init_index, len(lines))
            if len(lines[i]) > col and lines[i][col]
        ),
        (init_index, ""),
    )


def identify_epoch_segment(lines: list, init_index: int) -> _MinMaxTuple:
    """
    Return the bounds of the next epoch data line for ``StateVectorAccType`` or
    ``AttitudeStateType``.

    In KVN, each state-vector or attitude-state entry is a single space-delimited
    line whose first token is an epoch string (column 0).  Blank lines before the
    next entry are skipped.

    Returns a ``_MinMaxTuple(min, min+1)`` spanning exactly that one line, or a
    zero-width tuple ``(init_index, init_index)`` if no epoch line is found
    (signals the caller that this sub-block is exhausted).
    """
    data_index, first_col = _first_non_blank(lines, init_index, col=0)
    if _is_date_str(first_col):
        return _MinMaxTuple(data_index, data_index + 1)
    return _MinMaxTuple(init_index, init_index)


def identify_tracking_observation_segment(lines: list, init_index: int) -> _MinMaxTuple:
    """
    Return the bounds of the next ``TrackingDataObservationType`` line.

    TDM observation lines have the form ``KEYWORD = EPOCH value``, so the epoch
    string sits in column 1 (the value column), unlike state-vector lines where
    it is in column 0.  Blank lines are skipped.

    Returns a ``_MinMaxTuple(min, min+1)`` for that single line, or a zero-width
    tuple ``(init_index, init_index)`` if no observation line is found.
    """
    data_index, first_val = _first_non_blank(lines, init_index, col=1)
    if _is_date_str(first_val):
        return _MinMaxTuple(data_index, data_index + 1)
    return _MinMaxTuple(init_index, init_index)


def identify_covariance_segment(
    kw_list: list,
    init_index: int,
    keys: list,
    lines: list,
    single_element,
    prefix=None,
) -> _MinMaxTuple:
    """
    Identifies the min/max bounds for an ``OemCovarianceMatrixType`` block.

    First locates the keyword header lines via ``get_min_max_indices``, then extends
    the range to include any following numeric data rows.

    Parameters
    ----------
    kw_list : list
        Keyword list from the ``_NdmElement``.
    init_index : int
        Index where the search starts.
    keys : list
        Full KVN key list.
    lines : list
        Full KVN line list.
    single_element : str or None
        Passed through to ``get_min_max_indices``.
    prefix : str or None
        Optional key prefix (e.g. ``"USER_DEFINED"``).

    Returns a zero-width tuple ``(init_index, init_index)`` if no header is found.
    """
    temp_min_max = get_min_max_indices(
        kw_list, init_index, keys, prefix=prefix, single_elem=single_element
    )

    if temp_min_max.min == temp_min_max.max:
        return _MinMaxTuple(init_index, init_index)

    # Extend the range past the keyword header to include the numeric matrix rows.
    # Covariance data lines contain only space-separated floats (no "KEY = value"
    # structure), so we probe each line by attempting to parse its first token as a
    # float.  The loop stops as soon as a non-numeric line is encountered (e.g. the
    # next keyword or a blank line whose first token is empty/absent).
    i = temp_min_max.max
    while True:
        try:
            float(lines[i][0].split()[0])
            i += 1
        except (ValueError, IndexError):
            break

    return _MinMaxTuple(temp_min_max.min, i)


def identify_special_sub_segments(
    root_ndm_elem, keys: list, lines: list, init_index: int, prefix=None
) -> _MinMaxTuple:
    """
    Identifies the min/max bounds for a special-type NDM element.

    Dispatches to the appropriate handler based on the element's class name.
    Recognised classes are ``StateVectorAccType``, ``AttitudeStateType``,
    ``TrackingDataObservationType``, and ``OemCovarianceMatrixType``.

    Parameters
    ----------
    root_ndm_elem : _NdmElement
        The element whose bounds are being identified.
    keys : list
        Full KVN key list.
    lines : list
        Full KVN line list.
    init_index : int
        Index in ``keys``/``lines`` where the search starts.
    prefix : str or None
        Optional key prefix forwarded to the covariance handler.

    Returns
    -------
    _MinMaxTuple
        Min/max index bounds of the identified segment.
    """
    class_name = (
        root_ndm_elem.clazz.__name__
    )  # noqa: clazz is the attribute name on _NdmElement

    if class_name in ("StateVectorAccType", "AttitudeStateType"):
        return identify_epoch_segment(lines, init_index)

    elif class_name == "TrackingDataObservationType":
        return identify_tracking_observation_segment(lines, init_index)

    elif class_name == "OemCovarianceMatrixType":
        return identify_covariance_segment(
            root_ndm_elem.kw_list,
            init_index,
            keys,
            lines,
            root_ndm_elem.single_elem,
            prefix=prefix,
        )

    else:
        raise ValueError(
            f"Unknown Special Data Type ({class_name}) encountered "
            f"while identifying segments."
        )


def init_ndm_class(root_class: type, class_name: str) -> type:
    """
    Resolves and returns the class named `class_name` from the module of `root_class`.

    The xsdata-generated models use forward-reference strings for field types rather than
    direct class objects. This function resolves such a string back to the actual class
    by inspecting the module where `root_class` is defined (or its base class module).

    Parameters
    ----------
    root_class : type
        The dataclass whose module context is used to look up `class_name`.
        Typically a top-level NDM class (e.g. `Omm`, `Aem`) or one of its subclasses.
    class_name : str
        Name of the class to resolve (e.g. ``"OmmMetadata"``, ``"TdmSegment"``).

    Returns
    -------
    type
        The resolved class object.

    Raises
    ------
    UnboundLocalError
        If `class_name` is not found in the module of `root_class` or any imported module.
    """
    # xsdata puts all generated classes in the same module as their base class,
    # so start by looking at the base class's module.
    module_name = root_class.__bases__[0].__module__

    # For dynamically generated list subclasses the base module is reported as
    # "builtins". Fall back to the class's own module in that case.
    if module_name == "builtins":
        module_name = root_class.__module__

    # Import the module and enumerate its public classes.
    this_module = importlib.import_module(module_name)
    this_module_classes = inspect.getmembers(this_module, inspect.isclass)

    # Locate the target class by name; raise a clear error if it is absent.
    try:
        clazz = next(cls for name, cls in this_module_classes if name == class_name)
    except StopIteration:
        raise ValueError(f"Class '{class_name}' not found in module '{module_name}'")

    return clazz


def _lenient_class_factory(cls, params):
    """
    Instantiate ``cls`` from ``params``, filling any missing required field with ``None``.

    The generated dataclasses declare required fields (no default value) for
    sub-objects such as ``header`` and ``body``.  During KVN parsing these
    sub-objects are assembled one at a time and attached via ``setattr`` after
    construction, so they cannot all be supplied upfront.  This factory
    pre-fills every absent required field with ``None`` to avoid a
    ``TypeError`` at construction time.
    """
    for f in dataclasses.fields(cls):
        if f.init and f.name not in params:
            if (
                f.default is dataclasses.MISSING
                and f.default_factory is dataclasses.MISSING
            ):
                params[f.name] = None
    return cls(**params)


def init_root_ndm_object(clazz):
    """
    Instantiate a root NDM class (e.g. ``Apm``, ``Oem``) with ``None`` placeholders.

    Root classes have required fields (``header``, ``body``, etc.) that carry no
    default value.  The KVN parser builds these sub-objects separately and
    attaches them afterwards via ``setattr``, so this function pre-fills every
    required init field with ``None`` to allow construction without all values
    being available at once.
    """
    init_kwargs = {
        f.name: None
        for f in dataclasses.fields(clazz)
        if f.init
        and f.default is dataclasses.MISSING
        and f.default_factory is dataclasses.MISSING
    }
    return clazz(**init_kwargs)


def _unwrap_type(t):
    """
    Strip an ``Optional[X]`` or ``Union[X, None]`` wrapper and return ``X``.

    xsdata generates optional fields as ``Optional[SomeType]``, which is
    ``Union[SomeType, None]`` at runtime.  This helper extracts the concrete
    type so callers can work with it directly.  Non-union types are returned
    unchanged.  If the union contains only ``None`` (degenerate case), ``str``
    is returned as a safe fallback.
    """
    origin = getattr(t, "__origin__", None)
    if origin is types.UnionType or origin is typing.Union:
        args = [a for a in t.__args__ if a is not type(None)]
        return args[0] if args else str
    return t


def _coerce_value(raw_value, field_type):
    """
    Convert a raw KVN string value to the Python type expected by a dataclass field.

    Handles ``enum.Enum`` subclasses (looked up by value), ``float``, and
    ``int``.  Any other type is returned as-is (already a ``str``).
    ``Optional`` wrappers are stripped first via ``_unwrap_type``.
    """
    base = _unwrap_type(field_type)
    if isinstance(base, type) and issubclass(base, enum.Enum):
        return base(raw_value)
    if base is float:
        return float(raw_value)
    if base is int:
        return int(raw_value)
    return raw_value


def build_ndm_object(clazz, local_lines, prefix=None):
    """
    Build a dataclass instance directly from KVN ``local_lines`` without an XML
    round-trip.  Uses ``_lenient_class_factory`` so missing required fields are
    filled with ``None`` (to be set later by the subclass loop).

    Each entry in ``local_lines`` is a list of 2 or 3 strings:
      ``[key, value]``           - plain field or nested single-value dataclass
      ``[key, value, units]``    - nested dataclass that also carries a units attribute

    Special cases handled:
    - ``list[str]`` fields (e.g. COMMENT): values are accumulated into a list.
    - Nested leaf dataclasses (e.g. ``MomentType``): constructed from ``value`` +
      optional ``units`` attribute, without recursing into ``build_ndm_object``.
    - Prefix case (``UserDefinedType``): each item becomes a
      ``UserDefinedParameterType(parameter=..., value=...)`` appended to the list.
    """
    # Resolve forward-reference string annotations to actual type objects.
    # xsdata generates fields whose f.type is a plain string, not a type.
    resolved_hints = typing.get_type_hints(clazz)

    # Build a map from KVN keyword name → (field, resolved_type)
    name_to_field = {
        f.metadata.get("name"): (f, resolved_hints[f.name])
        for f in dataclasses.fields(clazz)
        if f.name in resolved_hints
    }

    params = {}

    if prefix:
        # USER_DEFINED_* items → list of UserDefinedParameterType
        entry = name_to_field.get(prefix)
        if entry is not None:
            list_field, list_type = entry
            item_clazz = _unwrap_type(list_type.__args__[0])
            entries = []
            for item in local_lines:
                if len(item) < 2 or not item[0].startswith(prefix + "_"):
                    continue
                param_name = item[0].replace(prefix + "_", "")
                entries.append(item_clazz(value=item[1], parameter=param_name))
            params[list_field.name] = entries
    else:
        for item in local_lines:
            key, raw_val = item[0], item[1]
            entry = name_to_field.get(key)
            if entry is None:
                continue

            field, resolved_type = entry
            base_type = _unwrap_type(resolved_type)

            if field.default_factory is not dataclasses.MISSING:
                # list field (e.g. COMMENT) — accumulate
                elem_type = _unwrap_type(base_type.__args__[0])
                params.setdefault(field.name, []).append(
                    _coerce_value(raw_val, elem_type)
                )
            elif dataclasses.is_dataclass(base_type):
                # Leaf nested dataclass (e.g. MomentType): value + optional units
                leaf_hints = typing.get_type_hints(base_type)
                leaf_fields = dataclasses.fields(base_type)
                value_field = leaf_fields[0]
                leaf_params = {
                    value_field.name: _coerce_value(
                        raw_val, leaf_hints[value_field.name]
                    )
                }
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
                params[field.name] = base_type(**leaf_params)
            else:
                params[field.name] = _coerce_value(raw_val, resolved_type)

    return _lenient_class_factory(clazz, params)
