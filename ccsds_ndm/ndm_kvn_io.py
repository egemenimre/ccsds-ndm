# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages KVN File I/O.

"""

import typing
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List

from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from ccsds_ndm.kvn_utils import (
    _lenient_class_factory,
    _MinMaxTuple,
    build_ndm_object,
    get_ccsds_kw_list,
    get_min_max_indices,
    identify_data_type,
    identify_special_sub_segments,
    init_root_ndm_object,
    is_class,
    is_id_or_version,
    is_list,
)

_special_extraction_classes = ["AttitudeStateType"]

_special_identification_classes = [
    "StateVectorAccType",
    "OemCovarianceMatrixType",
    "AttitudeStateType",
    "TrackingDataObservationType",
]
"""Classes whose KVN segment bounds require special identification logic.

These NDM data types do not follow the standard ``Key = Value [unit]`` line
format, so ``identify_special_sub_segments`` is used instead of the generic
``get_min_max_indices``.
"""

_special_processing_classes = [
    "StateVectorAccType",
    "OemCovarianceMatrixType",
    "AemSegment",
    "AttitudeStateType",
    "TrackingDataObservationType",
]
"""Classes whose object construction requires special handling.

These NDM data types cannot be built by the standard ``build_ndm_object``
path, so ``__build_special_objects`` dispatches to dedicated builders.
"""

_special_output_header_classes = [
    "AemData",
    "AemMetadata",
    "OemMetadata",
    "OemCovarianceMatrixType",
    "TdmMetadata",
    "TdmData",
]
"""Classes that require special header-section handling during KVN output."""

_special_output_data_classes = [
    "StateVectorAccType",
    "OemCovarianceMatrixType",
    "TrackingDataObservationType",
    "AttitudeStateType",
]
"""Classes that require special data-section handling during KVN output."""

_deleted_keywords = {
    "Oem": ["META_START", "META_STOP", "COVARIANCE_START", "COVARIANCE_STOP"],
    "Aem": ["META_START", "META_STOP", "DATA_START", "DATA_STOP"],
    "Tdm": ["META_START", "META_STOP", "DATA_START", "DATA_STOP"],
}
"""Section-delimiter keywords that must be stripped before parsing.

These structural markers (e.g. ``META_START``/``META_STOP``) are valid KVN
syntax but have no counterpart in the xsdata model and would cause key
mismatches if left in the ``_keys`` / ``_lines`` lists.
"""


@dataclass
class _NdmElement:
    """
    A node in the internal object tree that mirrors the NDM class hierarchy.

    Each ``_NdmElement`` corresponds to one dataclass in the xsdata-generated
    model.  The tree is built once by ``_init_object_map`` / ``_extract_object_submap``
    and then used in two passes:

    1. **Identification** (``_identify_segments``): ``min_max`` is filled with the
       line-index range in ``_lines`` that belongs to this node.
    2. **Construction** (``_build_object``): ``min_max`` is used to slice
       ``_lines`` and build the actual dataclass instance.

    Attributes
    ----------
    name : str
        Field name as declared in the parent dataclass (e.g. ``"header"``,
        ``"segment"``, ``"stateVector"``).
    clazz : type
        The dataclass type this element represents (e.g. ``OpmHeader``).
    subclass_list : list[_NdmElement]
        Child nodes corresponding to nested class fields.
    kw_list : list[str]
        All KVN keyword strings recognised by this node (e.g. ``["EPOCH", "X", "Y"]``).
    subname_list : list[str]
        Field names of all direct children, including ``"id"`` and ``"version"``.
    is_list : bool
        ``True`` when this node represents a repeatable field (``list[X]``).
    single_elem : str or None
        Set on "edge" wrapper classes (e.g. ``PositionType``) that contain a
        single value field plus optional units; holds the units attribute name.
    min_max : _MinMaxTuple or None
        Inclusive start / exclusive end indices into ``_lines`` for this node.
        ``None`` until the identification pass runs.
    special_data : dict
        Scratch space used by special builders (e.g. the AEM attitude-type
        template stored under ``"template"``).
    """

    name: str
    clazz: type
    subclass_list: list
    kw_list: list
    subname_list: list
    is_list: bool = False
    single_elem: str | None = None
    min_max: _MinMaxTuple | None = None
    special_data: Dict[str, Any] = field(default_factory=dict)


class NdmKvnIo:
    """
    Unified I/O Model for KVN input and output.
    """

    _keys: List[str] = []
    _lines: List[List[str]] = []

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
        with open(kvn_read_file_path, "r") as f:
            kvn_source = f.read()

        return self.from_string(kvn_source)

    def from_string(self, kvn_source: str):
        """
        Parse a KVN string and return the corresponding NDM object tree.

        This is the main entry point for string-based input and is called by
        ``from_path`` after reading the file.  It orchestrates the four-phase
        pipeline:

        1. **Pre-processing** — tokenise every line into ``[key, value, unit?]``
           tokens and populate ``_lines`` / ``_keys``.
        2. **Type identification** — read the ``CCSDS_*_VERS`` header to
           determine the NDM class (e.g. ``Omm``, ``Oem``).
        3. **Object-map initialisation** — walk the class hierarchy to build
           the ``_NdmElement`` tree that describes every expected field.
        4. **Segment identification** — match each ``_NdmElement`` node to the
           line-index range in ``_lines`` that belongs to it.
        5. **Object construction** — slice ``_lines`` per node and instantiate
           the actual dataclass objects.

        Parameters
        ----------
        kvn_source : str
            Raw KVN text (may contain Windows or Unix line endings).

        Returns
        -------
        object
            Fully populated NDM dataclass instance (e.g. ``Omm``, ``Oem``).
        """
        # Phase 1: tokenise every line into [key, value, unit?] lists
        self._pre_process_kvn_data(kvn_source)

        # Phase 2: identify the NDM type from the CCSDS_*_VERS header
        ndm_type = identify_data_type(self._lines)
        ndm_class = ndm_type.clazz

        # Phase 3: strip section-delimiter keywords that have no model counterpart
        # (e.g. META_START/META_STOP for Oem, Aem, Tdm)
        if ndm_class.__name__ in _deleted_keywords.keys():
            deleted_keys = _deleted_keywords[ndm_class.__name__]
            self._keys = [key for key in self._keys if key not in deleted_keys]
            self._lines = [line for line in self._lines if line[0] not in deleted_keys]

        # Phase 4: build the _NdmElement tree mirroring the class hierarchy
        self._init_object_map(ndm_class)

        # Phase 5: assign line-index ranges to every node in the tree
        self._identify_segments()

        # Phase 6: instantiate dataclass objects from the sliced lines
        return self._build_object()

    def _pre_process_kvn_data(self, kvn_source):
        """
        Tokenise a raw KVN string into ``_lines`` and ``_keys``.

        Each line is converted to a list of 1–3 strings:

        * Blank lines → ``[""]``
        * ``COMMENT`` lines → ``["COMMENT", "<text>"]``
        * Data lines → ``["KEY", "value"]`` or ``["KEY", "value", "unit"]``

        The ``CCSDS_*_VERS`` version header is split into two synthetic rows so
        the rest of the parser can treat ``id`` and ``version`` as ordinary
        fields:

        * Row 0: ``["id",      "CCSDS_OMM_VERS"]``
        * Row 1: ``["version", "2.0"]``

        Parameters
        ----------
        kvn_source : str
            Raw KVN text (may start with blank lines before the ``CCSDS_`` line).
        """

        input_lines = kvn_source.split("\n")

        id_line_not_found = True

        lines = []
        for line in input_lines:
            # Strip surrounding whitespace from every raw line
            line = line.strip()

            # Once we see the CCSDS_ header, stop skipping leading blank lines
            if line.startswith("CCSDS_"):
                id_line_not_found = False

            # Drop blank lines that appear before the CCSDS_ header
            if id_line_not_found and not line.strip():
                continue

            # --- COMMENT lines ---
            if line.startswith("COMMENT"):
                line = ["COMMENT", line[7:].strip()]

                # Some files write "COMMENT = text" — strip the leading "="
                if line[1].startswith("="):
                    line[1] = line[1][1:].strip()
            else:
                # --- Data / blank lines ---

                # Split on the first "=" to get [key, rest]
                line = line.split("=", maxsplit=1)

                # Extract trailing units if the value ends with "]"
                if len(line) == 2 and line[1].rstrip().endswith("]"):
                    text = line[1]
                    splitter_index = line[1].find("[")
                    if splitter_index >= 0:
                        line[1] = text[0:splitter_index]
                        unit = text[splitter_index:].replace("[", "").replace("]", "")
                        line.append(unit)

            # Strip surrounding whitespace from every token
            line = [item.strip() for item in line]

            lines.append(line)

        # Duplicate the CCSDS_*_VERS line so we can expose both the id string
        # and the version number as separate "fields" expected by the model.
        lines.insert(1, lines[0])

        id_str = lines[0][0]  # e.g. "CCSDS_OMM_VERS"
        version_str = lines[0][1]  # e.g. "2.0"

        lines[0] = ["id", id_str]
        lines[1] = ["version", version_str]

        self._lines = lines

        # Build the flat key list for fast O(1) membership checks and index lookups
        self._keys = [line[0] for line in lines]

    def _init_object_map(self, root_class):
        """
        Build the ``_NdmElement`` tree that mirrors the NDM class hierarchy.

        Delegates to ``_extract_object_submap`` for the recursive walk, then
        appends ``"id"`` and ``"version"`` to the root node's keyword list so
        the version-header lines are claimed by the root element during segment
        identification.

        Parameters
        ----------
        root_class : type
            Top-level NDM dataclass (e.g. ``Omm``, ``Aem``, ``Cdm``).
        """

        root_tag = root_class.id

        self.object_tree = self._extract_object_submap(root_tag, root_class)

        # The CCSDS_*_VERS line is pre-processed into synthetic "id" and
        # "version" rows; register them so the root node claims those lines.
        self.object_tree.kw_list.extend(["id", "version"])

    def _extract_object_submap(
        self, root_tag: str, root_class, root_is_list=False
    ) -> _NdmElement:
        """
        Recursively build a ``_NdmElement`` node for ``root_class`` and all its children.

        Walks the dataclass field hierarchy to populate ``kw_list`` (the KVN
        keywords this node owns) and ``subclass_list`` (child nodes for nested
        class fields).  Two special cases alter the normal walk:

        * **Edge classes** (classes that have a ``"value"`` field, e.g.
          ``PositionType``) — they wrap a single scalar plus optional units.
          Their inner keywords are absorbed into the parent's ``kw_list`` and
          no child node is created; ``single_elem`` is set to the units
          attribute name instead.
        * **Non-dataclass types** (enums, ``Decimal``, etc.) — they have no
          ``__dataclass_fields__``; an empty node is returned.

        Parameters
        ----------
        root_tag : str
            Field name used to address this node in the parent (e.g. ``"header"``,
            ``"segment"``).  The class-level ``id`` attribute is used for the
            outermost call.
        root_class : type
            The dataclass (or enum / scalar) being described.
        root_is_list : bool
            ``True`` when this field is declared as ``list[root_class]`` in the
            parent, meaning multiple instances may appear in the KVN file.

        Returns
        -------
        _NdmElement
            Fully populated node ready for the identification and build passes.
        """

        # Collect only the all-uppercase keyword names (KVN tags); mixed-case
        # names are nested class fields handled via subclass_list.
        kw_list = [kw for kw in get_ccsds_kw_list(root_class) if kw.isupper()]

        single_elem = None

        # Resolve forward-reference string annotations to actual type objects
        hints = typing.get_type_hints(root_class)

        if "__dataclass_fields__" in vars(root_class).keys():

            # Collect all field names declared on this dataclass (e.g. "header",
            # "body", "id", "version") for use as subname_list.
            subname_list = [
                key for key in vars(root_class)["__dataclass_fields__"].keys()
            ]

            # Work only with non-id/version fields; id and version are synthetic
            # rows handled separately at the root level.
            names_fields = {
                name: field_data
                for name, field_data in vars(root_class)["__dataclass_fields__"].items()
                if not is_id_or_version(name)
            }

            # Identify fields that are nested NDM classes (not leaf KVN keywords)
            # and resolve their concrete type through Optional / list wrappers.
            names_classes = []
            for name, field_data in names_fields.items():

                if is_class(field_data):
                    t = hints[name]
                    args = typing.get_args(t)

                    if args:
                        # Optional[X] → (X, NoneType) or list[X] → (X,)
                        clazz = next(
                            a for a in args if a is not type(None) and a is not list
                        )
                    else:
                        # Plain (non-wrapped) class annotation
                        clazz = t

                    names_classes.append((name, clazz, is_list(field_data)))

            if "value" in subname_list:
                # Edge/wrapper class (e.g. PositionType): it contains a scalar
                # "value" plus an optional "units" attribute and possibly one
                # more nested class (e.g. an enum for the frame name).
                # Absorb that inner class's keywords into this node's kw_list
                # and record the units attribute name in single_elem.
                single_name_class = [
                    (name, clazz)
                    for (name, clazz, is_class) in names_classes
                    if name != "value" and name != "units"
                ]

                single_elem = single_name_class[0][0]

                # Flatten keywords from nested classes into this node
                lower_level_kw_list = [
                    get_ccsds_kw_list(clazz) for (name, clazz) in single_name_class
                ]
                flatten_list = [item for subl in lower_level_kw_list for item in subl]
                kw_list.extend(flatten_list)

                # No child _NdmElement nodes — all data is in kw_list
                name_class_sublist: List[_NdmElement] = []
            else:
                # Normal class: recurse into each nested-class field to build
                # a child _NdmElement node.
                name_class_sublist = []
                for name, clazz, is_list_flag in names_classes:
                    name_class_sublist.append(
                        self._extract_object_submap(
                            name, clazz, root_is_list=is_list_flag
                        )
                    )

        else:
            # No __dataclass_fields__: enum, Decimal, or other scalar type.
            # Return an empty node; the parent handles the value directly.
            name_class_sublist = []
            subname_list = []

        object_tree = _NdmElement(
            root_tag,
            root_class,
            name_class_sublist,
            kw_list,
            subname_list,
            single_elem=single_elem,
            is_list=root_is_list,
        )

        return object_tree

    def _identify_segments(self):
        """
        Assign line-index ranges to every node in the ``_NdmElement`` tree.

        Drives the recursive ``__identify_sub_segments`` call starting from the
        root node and stores the resulting ``_MinMaxTuple`` on each node.  After
        this pass, every node's ``min_max`` indicates which slice of ``_lines``
        belongs to it and should be used during object construction.
        """

        root_ndm_elem = self.object_tree

        max_index, root_min_max = self.__identify_sub_segments(
            root_ndm_elem, self._keys, self._lines
        )
        root_ndm_elem.min_max = root_min_max

    def __identify_sub_segments(self, root_ndm_elem, keys, lines, init_index=0):
        """
        Recursively assign line-index ranges to ``root_ndm_elem`` and its children.

        First determines the range of ``keys`` / ``lines`` that belongs to
        ``root_ndm_elem`` itself (its own KVN keywords), then delegates to
        ``__identify_sub_sub_segments`` to process any child nodes.

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            Node whose bounds are being determined.
        keys : list[str]
            Flat list of KVN key strings (parallel to ``lines``).
        lines : list[list[str]]
            Tokenised KVN lines (each entry is ``[key, value, ...]``).
        init_index : int
            Row index in ``keys``/``lines`` to start searching from.

        Returns
        -------
        (int, _MinMaxTuple)
            ``(max_index, root_min_max)`` where ``root_min_max`` is the
            inclusive-start / exclusive-end range for this node and
            ``max_index`` is the furthest index reached by this node and all
            its children (the starting point for the next sibling search).
        """

        # USER_DEFINED_* keys use a common prefix rather than fixed names
        if root_ndm_elem.clazz.__name__ == "UserDefinedType":
            prefix = "USER_DEFINED"
        else:
            prefix = None

        # Special types (state vectors, covariance, TDM observations, AEM
        # attitude states) cannot be located by keyword matching alone
        if root_ndm_elem.clazz.__name__ in _special_identification_classes:
            root_min_max = identify_special_sub_segments(
                root_ndm_elem, keys, lines, init_index, prefix
            )
        else:
            # Normal case: locate the node's keywords in the key list
            root_min_max = get_min_max_indices(
                root_ndm_elem.kw_list,
                init_index,
                keys,
                prefix=prefix,
                single_elem=root_ndm_elem.single_elem,
            )

        # Advance past this node's own lines before searching for children
        init_index = root_min_max.max
        max_index = init_index

        if root_ndm_elem.subclass_list:
            # Recurse into child nodes, starting where this node ended
            max_index = self.__identify_sub_sub_segments(
                root_ndm_elem, root_min_max, keys, lines, init_index
            )

        return max_index, root_min_max

    def __identify_sub_sub_segments(
        self, root_ndm_elem, root_min_max, keys, lines, init_index
    ):
        """
        Identify line-index ranges for all direct children of ``root_ndm_elem``.

        Iterates over the expected child types in ``root_ndm_elem.subclass_list``
        and dispatches each to either ``__identify_list`` (for repeatable fields)
        or ``__identify_sub_segments`` (for singular fields), advancing
        ``init_index`` sequentially so each child starts where the previous one
        ended.

        A special retry is performed for singular fields that come back empty:
        some deeply nested leaf classes (e.g. ``UserDefinedType``) embed their
        keywords inside the parent's line range rather than after it, so the
        search is re-tried from ``root_min_max.min`` in that case (without
        updating ``max_index`` to avoid advancing the pointer).

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            Parent node whose children are being identified.
        root_min_max : _MinMaxTuple
            Line-index range of ``root_ndm_elem`` itself (used as fallback
            start for the nested-leaf retry).
        keys : list[str]
            Flat KVN key list.
        lines : list[list[str]]
            Tokenised KVN line list.
        init_index : int
            Row index to start searching children from.

        Returns
        -------
        int
            Furthest line index reached across all children.
        """

        generated_subclasses: List[_NdmElement] = []
        expected_types = [subclass for subclass in root_ndm_elem.subclass_list]

        max_index = init_index

        for subclass in expected_types:

            if subclass.is_list:
                # Repeatable field: consume as many occurrences as exist
                max_index = self.__identify_list(
                    subclass, keys, lines, init_index, generated_subclasses
                )
                init_index = max_index
            else:
                # Singular field: identify once and advance
                max_index, subclass_min_max = self.__identify_sub_segments(
                    subclass, keys, lines, init_index
                )
                subclass.min_max = subclass_min_max
                init_index = max_index

                if (
                    subclass.min_max.min == subclass.min_max.max
                    and not subclass.subclass_list
                ):
                    # Empty result with no children: this may be a leaf class
                    # whose keywords are embedded within the parent's range.
                    # Retry from the parent start without advancing max_index.
                    mock_max_index, subclass_min_max = self.__identify_sub_segments(
                        subclass, keys, lines, root_min_max.min
                    )
                    subclass.min_max = subclass_min_max

                generated_subclasses.append(subclass)

        # Replace the template subclass list with the identified instances
        root_ndm_elem.subclass_list = generated_subclasses

        return max_index

    def __identify_list(self, subclass, keys, lines, init_index, generated_subclasses):
        """
        Identify all occurrences of a repeatable (list) field in the KVN data.

        Repeatedly calls ``__identify_sub_segments`` for ``subclass`` until no
        more matches are found or a gap containing non-blank, non-comment keys
        is detected (which signals that the remaining lines belong to a different
        block).  Each matched occurrence is appended to ``generated_subclasses``.

        The loop stops early if the end of the file is reached or if the returned
        range is empty (``min == max``).

        Parameters
        ----------
        subclass : _NdmElement
            Template node describing the repeatable element type.  A fresh copy
            (or a re-extracted submap) is used for each iteration so that
            ``min_max`` from previous iterations does not bleed through.
        keys : list[str]
            Flat KVN key list.
        lines : list[list[str]]
            Tokenised KVN line list.
        init_index : int
            Row index to start searching from.
        generated_subclasses : list[_NdmElement]
            Accumulator list; matched occurrences are appended here so the
            caller can splice them into the parent's ``subclass_list``.

        Returns
        -------
        int
            Furthest line index reached (i.e. the exclusive end of the last
            matched occurrence, or ``init_index`` if nothing was found).
        """

        has_elements = True
        last_max_index = max_index = init_index

        subclass_list = []

        # loop as long as there is a next element that belongs to the list
        while has_elements:

            # start with a clean object with the subclass type
            if subclass.subclass_list:
                clean_obj = self._extract_object_submap(subclass.name, subclass.clazz)
            else:
                clean_obj = deepcopy(subclass)

            # identify subclasses and find limits
            max_index, subclass_min_max = self.__identify_sub_segments(
                clean_obj, keys, lines, init_index
            )

            if max_index == subclass_min_max.min == subclass_min_max.max:
                # list is completed, no more elements
                has_elements = False
            elif subclass_min_max.min > last_max_index and any(
                keys[i] not in ("", "COMMENT")
                for i in range(last_max_index, subclass_min_max.min)
            ):
                # There is a gap containing real (non-blank, non-comment) keys —
                # those belong to another block; stop the list here.
                has_elements = False
                max_index = last_max_index
            else:
                # found lines are valid elements of this list, add them
                clean_obj.min_max = subclass_min_max
                init_index = max_index
                last_max_index = max_index
                subclass_list.append(clean_obj)

                if max_index >= len(lines):
                    # End of file reached, stop the while loop
                    has_elements = False

        # insert resulting list into expected subclasses
        generated_subclasses.extend(subclass_list)

        return max_index

    def _build_object(self):
        """
        Construct the NDM object tree from the identified line-index ranges.

        Creates an ``XmlParser`` configured with ``_lenient_class_factory`` so
        that required-but-missing constructor arguments (e.g. ``ApmBody.segment``
        which must be a non-empty list) are pre-filled with ``None`` placeholders.
        The recursive ``__build_object_tree`` call replaces these placeholders with
        real objects via ``setattr`` as it processes each child node.

        Returns
        -------
        object
            Fully populated NDM dataclass instance (e.g. ``Omm``, ``Aem``).
        """
        # prepare parser with a lenient class factory that passes None for any
        # required init fields missing from the XML fragment (e.g. ApmBody.segment).
        # The subclass loop in __build_object_tree fills them in via setattr afterwards.
        parser = XmlParser(
            config=ParserConfig(
                fail_on_unknown_properties=True,
                class_factory=_lenient_class_factory,
            )
        )

        root_ndm_elem = self.object_tree
        ndm_object = self.__build_object_tree(root_ndm_elem, self._lines, parser)

        return ndm_object

    def __build_object_tree(self, root_ndm_elem, full_lines, parser):
        """
        Recursively build the NDM dataclass instance for ``root_ndm_elem``.

        Slices ``full_lines`` using the node's ``min_max`` bounds, filters the
        slice to only the keywords owned by this node, then dispatches to the
        appropriate builder:

        * **Special types** (``_special_processing_classes``) → ``__build_special_objects``
        * **Pure containers** (id/version root, or no data lines) → ``init_root_ndm_object``
        * **Single-element wrappers** (``single_elem`` set) → ``_xmlify_single_elem``
          followed by ``parser.from_bytes``
        * **Normal data nodes** → ``build_ndm_object``

        After building ``root_ndm_elem``'s own object, the method recurses into
        each child in ``subclass_list`` and attaches the result via ``setattr``
        (or ``list.append`` for list fields).

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            Node to build; its ``min_max`` must already be set.
        full_lines : list[list[str]]
            The complete tokenised KVN line list (not just the local slice).
        parser : XmlParser
            Lenient XML parser used for single-element wrapper types.

        Returns
        -------
        object or None
            Populated NDM dataclass instance, or ``None`` if the node has no
            content and no children.
        """
        # check for prefix
        if root_ndm_elem.clazz.__name__ == "UserDefinedType":
            prefix = "USER_DEFINED"
        else:
            prefix = None

        # init root object
        local_lines = full_lines[root_ndm_elem.min_max.min : root_ndm_elem.min_max.max]
        kw_list = root_ndm_elem.kw_list

        if not local_lines and not root_ndm_elem.subclass_list:
            # item has no subclasses and no content, just skip it
            return None
        else:

            # check for special types
            if root_ndm_elem.clazz.__name__ in _special_processing_classes:
                ndm_object = self.__build_special_objects(
                    root_ndm_elem, kw_list, local_lines
                )
            else:
                # not a special type, proceed normally
                if not prefix:
                    # intersect list with keywords as a final check
                    # protects from wrong keywords on nested structures
                    # if prefix is present, then
                    local_lines = [line for line in local_lines if line[0] in kw_list]

                if not local_lines and not root_ndm_elem.subclass_list:
                    # item has no subclasses and no content, just skip it
                    return None

                if kw_list == ["id", "version"] or not local_lines:
                    # Pure container: either the outermost root (id/version only) or a
                    # node with no data lines. Required fields are filled in by the
                    # subclass loop below via setattr.
                    ndm_object = init_root_ndm_object(root_ndm_elem.clazz)

                elif root_ndm_elem.single_elem:
                    # Process as single element
                    xml_data = _xmlify_single_elem(
                        root_ndm_elem.name, local_lines, root_ndm_elem.single_elem
                    )
                    ndm_object = parser.from_bytes(xml_data, root_ndm_elem.clazz)
                else:
                    # Has data lines: build directly without XML round-trip.
                    ndm_object = build_ndm_object(
                        root_ndm_elem.clazz, local_lines, prefix
                    )

        # fill lower level objects
        for subclass in root_ndm_elem.subclass_list:
            subobject = self.__build_object_tree(subclass, full_lines, parser)
            if isinstance(getattr(ndm_object, subclass.name), list):
                if subobject:
                    # this is a list, add the new element
                    getattr(ndm_object, subclass.name).append(subobject)
            else:
                # this is not a list, just replace the data
                setattr(ndm_object, subclass.name, subobject)

        return ndm_object

    __att_types = {
        "QUATERNION": "quaternion_state",
        "QUATERNION/DERIVATIVE": "quaternion_derivative",
        "QUATERNION/RATE": "quaternion_euler_rate",
        "EULER_ANGLE": "euler_angle",
        "EULER_ANGLE/RATE": "euler_angle_rate",
        "SPIN": "spin",
        "SPIN/NUTATION": "spin_nutation",
    }

    __euler_angle_id = {"1": "X_ANGLE", "2": "Y_ANGLE", "3": "Z_ANGLE"}
    __euler_rate_id = {"1": "X_RATE", "2": "Y_RATE", "3": "Z_RATE"}

    def __build_special_objects(self, root_ndm_elem: _NdmElement, kw_list, lines):
        """
        Build an NDM object for a type that requires non-standard construction.

        Dispatches to a dedicated builder for each class named in
        ``_special_processing_classes``:

        * **AemSegment** — pure container; delegates sub-object preparation to
          ``__prepare_aemsegment_sub_objects`` then creates an empty root via
          ``init_root_ndm_object``.
        * **AttitudeStateType** — single packed data line; delegates to
          ``__build_att_segment_data``.
        * **StateVectorAccType** — single space-separated data line; zips the
          node's ``kw_list`` with the split tokens to form synthetic key-value
          pairs and calls ``build_ndm_object``.
        * **OemCovarianceMatrixType** — lower-triangular matrix rows mixed with
          normal KVN lines; separates numeric rows from keyword rows, flattens
          the matrix values, and calls ``build_ndm_object``.
        * **TrackingDataObservationType** — single ``EPOCH <value>`` line; zips
          ``["EPOCH", <observation-type-key>]`` with the split tokens.

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            Node whose class name is in ``_special_processing_classes``.
        kw_list : list[str]
            Ordered keyword list for this node (used as zip keys for packed lines).
        lines : list[list[str]]
            Tokenised lines belonging to this node's ``min_max`` slice.

        Returns
        -------
        object
            Populated NDM dataclass instance for the special type.

        Raises
        ------
        ValueError
            If ``root_ndm_elem.clazz.__name__`` is not in the known dispatch table.
        """

        if root_ndm_elem.clazz.__name__ == "AemSegment":
            # Pure container: subclasses fill metadata and data via setattr.
            self.__prepare_aemsegment_sub_objects(root_ndm_elem)
            ndm_object = init_root_ndm_object(root_ndm_elem.clazz)

        elif root_ndm_elem.clazz.__name__ == "AttitudeStateType":
            ndm_object = self.__build_att_segment_data(root_ndm_elem, lines)

        elif root_ndm_elem.clazz.__name__ == "StateVectorAccType":
            synth_lines = list(zip(kw_list, lines[0][0].split()))
            ndm_object = build_ndm_object(root_ndm_elem.clazz, synth_lines)

        elif root_ndm_elem.clazz.__name__ == "OemCovarianceMatrixType":
            # Stacked covariance data
            datalines = [line[0].split() for line in lines if not line[0].isalpha()]
            kvnlines = [line for line in lines if line[0].isalpha()]
            data_list = [item for sublist in datalines for item in sublist]
            synth_lines = list(zip(kw_list[3:], data_list))
            kvnlines.extend(synth_lines)
            ndm_object = build_ndm_object(root_ndm_elem.clazz, kvnlines)

        elif root_ndm_elem.clazz.__name__ == "TrackingDataObservationType":
            synth_lines = list(zip(["EPOCH", lines[0][0]], lines[0][1].split()))
            ndm_object = build_ndm_object(root_ndm_elem.clazz, synth_lines)

        else:
            raise ValueError(
                f"Unknown Special Data Type ({root_ndm_elem.clazz}) encountered "
                f"while building object."
            )

        return ndm_object

    def __prepare_aemsegment_sub_objects(self, root_ndm_elem):
        """
        Prune unused attitude-state sub-types from an AEM segment node.

        An AEM segment can hold one of several attitude representations
        (quaternion, Euler, spin, …).  The actual type is declared by the
        ``ATTITUDE_TYPE`` metadata key and, for quaternion variants, the order
        of components is declared by ``QUATERNION_TYPE``.  For Euler/spin
        variants the axis order comes from ``EULER_ROT_SEQ``.

        This method:

        1. Reads ``ATTITUDE_TYPE`` (and the relevant companion key) from
           ``_lines`` to determine the active representation.
        2. Builds a ``kw_template`` — the ordered list of column names for each
           packed attitude-state data line (e.g. ``["EPOCH", "Q1", "Q2", ...]``).
        3. Stores ``kw_template`` in every ``AttitudeStateType`` node's
           ``special_data["template"]`` so ``__build_att_segment_data`` can
           unpack each line.
        4. Drops all sub-nodes from each ``AttitudeStateType`` except the one
           matching the active attitude type, so the builder does not attempt to
           construct unused representations.

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            The ``AemSegment`` node.  Its ``min_max.max`` is used as the start
            index when searching for ``ATTITUDE_TYPE`` in ``_keys``.
        """

        att_states = root_ndm_elem.subclass_list[1].subclass_list

        # Find the Attitude Type line within the segment
        att_type_line_index = self._keys.index(
            "ATTITUDE_TYPE", root_ndm_elem.min_max.max
        )
        att_type_key = self._lines[att_type_line_index][1]
        att_type_value = self.__att_types.get(att_type_key)

        kw_template = ["EPOCH"]

        if att_type_key.startswith("QUATERNION"):
            q_type_line_index = self._keys.index(
                "QUATERNION_TYPE", root_ndm_elem.min_max.max
            )
            q_type_key = self._lines[q_type_line_index][1]

            if q_type_key == "FIRST":
                kw_template.extend(["QC", "Q1", "Q2", "Q3"])
            else:
                kw_template.extend(["Q1", "Q2", "Q3", "QC"])

            if att_type_key.endswith("DERIVATIVE"):
                if q_type_key == "FIRST":
                    kw_template.extend(["QC_DOT", "Q1_DOT", "Q2_DOT", "Q3_DOT"])
                else:
                    kw_template.extend(["Q1_DOT", "Q2_DOT", "Q3_DOT", "QC_DOT"])

        if att_type_key.startswith("EULER") or att_type_key.endswith("RATE"):
            eu_type_line_index = self._keys.index(
                "EULER_ROT_SEQ", root_ndm_elem.min_max.max
            )
            eu_type_key = self._lines[eu_type_line_index][1]

            if att_type_key.startswith("EULER"):
                kw_template.extend([self.__euler_angle_id[key] for key in eu_type_key])
            if att_type_key.endswith("RATE"):
                kw_template.extend([self.__euler_rate_id[key] for key in eu_type_key])

        # delete unused att types
        for att_state in att_states:
            att_state.special_data["template"] = kw_template
            att_state.subclass_list = [
                subclass
                for subclass in att_state.subclass_list
                if subclass.name == att_type_value
            ]
            att_state.subname_list = [
                subclass.name for subclass in att_state.subclass_list
            ]

    __xml_parser = XmlParser(config=ParserConfig(fail_on_unknown_properties=True))

    def __build_att_segment_data(self, root_ndm_elem, lines):
        """
        Build an ``AttitudeStateType`` object from a single packed KVN data line.

        Each AEM data line is a space-separated row of values (epoch + attitude
        components) with no explicit keys.  The column order was determined by
        ``__prepare_aemsegment_sub_objects`` and stored in
        ``root_ndm_elem.special_data["template"]``.

        Steps:

        1. Zip the template key list with the split tokens from the first (only)
           line to create synthetic ``(key, value)`` pairs — ``synth_lines``.
        2. Re-run segment identification on these synthetic lines so the child
           nodes get correct ``min_max`` bounds within the synthetic list.
        3. Recursively build the single active attitude sub-object via
           ``__build_object_tree`` (e.g. ``QuaternionStateType``).
        4. Wrap the sub-object in a bare ``AttitudeStateType`` instance via
           ``init_root_ndm_object`` + ``setattr``.
        5. Clear ``subclass_list`` / ``subname_list`` on the node so the caller's
           loop in ``__build_object_tree`` does not try to process children again.

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            The ``AttitudeStateType`` node with ``special_data["template"]`` set.
        lines : list[list[str]]
            The single packed data line belonging to this node.

        Returns
        -------
        object
            Populated ``AttitudeStateType`` dataclass instance.
        """

        # Merge data with template
        synth_lines = list(
            zip(root_ndm_elem.special_data["template"], lines[0][0].split())
        )

        # identify the line
        max_index, root_min_max = self.__identify_sub_segments(
            root_ndm_elem, root_ndm_elem.special_data["template"], synth_lines
        )
        root_ndm_elem.min_max = root_min_max

        # build object internal to att state
        internal_obj = self.__build_object_tree(
            root_ndm_elem.subclass_list[0], synth_lines, self.__xml_parser
        )

        att_state_obj = init_root_ndm_object(root_ndm_elem.clazz)
        setattr(att_state_obj, root_ndm_elem.subclass_list[0].name, internal_obj)

        # kill the subclasses, they are already processed
        root_ndm_elem.subclass_list = []
        root_ndm_elem.subname_list = []

        return att_state_obj


def _xmlify_single_elem(root_tag, item_list, param_name):
    """
    Serialise a single-element KVN wrapper line to an XML byte string.

    Edge classes such as ``PositionType`` wrap a scalar value plus an optional
    ``units`` attribute and one nested attribute (e.g. a frame name).  The KVN
    line for these looks like ``X = 6655.9942 [km]`` where ``"X"`` is the
    attribute that selects the inner field and ``"6655.9942"`` is the value.

    The produced XML fragment is then parsed by ``XmlParser.from_bytes`` to
    construct the actual dataclass instance.

    Parameters
    ----------
    root_tag : str
        XML element tag name (matches the field name in the parent class,
        e.g. ``"x"`` for the ``x`` field of ``StateVector``).
    item_list : list[list[str]]
        A one-element list containing the tokenised KVN line for this field,
        i.e. ``[[key, value]]`` or ``[[key, value, unit]]``.
    param_name : str
        Name of the XML attribute that holds ``key`` (the inner selector),
        e.g. ``"units"`` or the enum-frame attribute name.

    Returns
    -------
    bytes
        UTF-8 encoded XML fragment suitable for ``XmlParser.from_bytes``.
    """
    item = item_list[0]

    # create XML
    root = etree.Element(root_tag)

    root.text = item[1]
    root.attrib[param_name] = item[0]

    if len(item) > 2:
        # add units if available
        root.attrib["units"] = item[2]

    return etree.tostring(root, pretty_print=True)
