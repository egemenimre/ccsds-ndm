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
from ccsds_ndm.ndm_xml_io_old import NdmXmlIo

_special_extraction_classes = ["AttitudeStateType"]

_special_identification_classes = [
    "StateVectorAccType",
    "OemCovarianceMatrixType",
    "AttitudeStateType",
    "TrackingDataObservationType",
]
"""List of special classes with special data types in identification.

This lists the NDM special data types that do not conform to the `Key = Value [unit]` format.
"""

_special_processing_classes = [
    "StateVectorAccType",
    "OemCovarianceMatrixType",
    "AemSegment",
    "AttitudeStateType",
    "TrackingDataObservationType",
]
"""List of special classes with special data types in processing (object build).

This lists the NDM special data types that do not conform to the `Key = Value [unit]` format.
"""

_special_output_header_classes = [
    "AemData",
    "AemMetadata",
    "OemMetadata",
    "OemCovarianceMatrixType",
    "TdmMetadata",
    "TdmData",
]
_special_output_data_classes = [
    "StateVectorAccType",
    "OemCovarianceMatrixType",
    "TrackingDataObservationType",
    "AttitudeStateType",
]

_deleted_keywords = {
    "Oem": ["META_START", "META_STOP", "COVARIANCE_START", "COVARIANCE_STOP"],
    "Aem": ["META_START", "META_STOP", "DATA_START", "DATA_STOP"],
    "Tdm": ["META_START", "META_STOP", "DATA_START", "DATA_STOP"],
}
"""List of keywords to be deleted from files. They interfere with the processing."""


@dataclass
class _NdmElement:
    """
    NDM element and sub elements data.

    Stores variable name, class, keywords, subclasses and
    "lines in the KVN file" data.
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
        # parse file to fill lines and keys lists
        self._pre_process_kvn_data(kvn_source)

        #  Identify data type
        ndm_type = identify_data_type(self._lines)
        ndm_class = ndm_type.clazz

        # Delete unnecessary keywords if necessary
        if ndm_class.__name__ in _deleted_keywords.keys():
            deleted_keys = _deleted_keywords.get(ndm_class.__name__)
            self._keys = [key for key in self._keys if key not in deleted_keys]
            self._lines = [line for line in self._lines if line[0] not in deleted_keys]

        # Init object map
        self._init_object_map(ndm_class)

        # identify the segments
        self._identify_segments()

        # build the object
        return self._build_object()

    def _pre_process_kvn_data(self, kvn_source):
        """
        Processes the KVN data string to fill an internal list of key-value pairs.

        Parameters
        ----------
        kvn_source : str
            input string containing KVN data
        """

        input_lines = kvn_source.split("\n")

        id_line_not_found = True

        lines = []
        for line in input_lines:
            # strip spaces around the line
            line = line.strip()

            # Look for the CCSDS_ line
            if line.startswith("CCSDS_"):
                id_line_not_found = False

            # skip first empty lines, until CCSDS_ line is found
            if id_line_not_found and not line.strip():
                continue

            # TODO fix it
            # skip all empty lines
            # if not line.strip():
            #     continue

            # process Comment lines first
            if line.startswith("COMMENT"):
                line = ["COMMENT", line[7:].strip()]

                # sometimes comment line starts with an "=" sign, delete this
                if line[1].startswith("="):
                    line[1] = line[1][1:].strip()
            else:
                # This is not a comment line

                # split the data lines with "=" as delimiter
                line = line.split("=", maxsplit=1)

                # parse data lines with units
                if len(line) == 2 and line[1].rstrip().endswith("]"):
                    text = line[1]
                    splitter_index = line[1].find("[")
                    if splitter_index >= 0:
                        line[1] = text[0:splitter_index]
                        # strip square braces
                        unit = text[splitter_index:].replace("[", "").replace("]", "")
                        line.append(unit)

            # finally, strip each element of spaces
            line = [item.strip() for item in line]

            # add to list
            lines.append(line)

        # modify lines and keys for id and header
        lines.insert(1, lines[0])

        # The line that starts with "CCSDS_" should be the first line.
        id_str = lines[0][0]
        version_str = lines[0][1]

        lines[0] = ["id", id_str]
        lines[1] = ["version", version_str]

        self._lines = lines

        # extract keywords for easy access
        self._keys = [line[0] for line in lines]

    def _init_object_map(self, root_class):
        """
        Initialises and fills the internal object map using the class information.

        Parameters
        ----------
        root_class
            Root class of type Omm, Aem, Cdm etc.

        """

        root_tag = root_class.id

        self.object_tree = self._extract_object_submap(root_tag, root_class)

        # add id and version keyword info
        self.object_tree.kw_list.extend(["id", "version"])

    def _extract_object_submap(
        self, root_tag: str, root_class, root_is_list=False
    ) -> _NdmElement:
        """
        Extracts the object submap and all elements in the tree recursively.

        Parameters
        ----------
        root_tag : str
            Variable name of the root class ("omm", "aem", "cdm" etc.)
        root_class
            Root class of type Omm, Aem, Cdm etc.
        root_is_list : bool
            True if root is of type list, false otherwise

        Returns
        -------
        _NdmElement
            NDM object tree

        """

        kw_list = [kw for kw in get_ccsds_kw_list(root_class) if kw.isupper()]

        single_elem = None

        # Resolves all string annotations to actual class objects
        hints = typing.get_type_hints(root_class)

        if "__dataclass_fields__" in vars(root_class).keys():
            # fill requisite data to populate the NdmElement

            # Find dataclass keys like "header", "body", "id", "version"
            # They correspond to the fields under this root class
            subname_list = [
                key for key in vars(root_class)["__dataclass_fields__"].keys()
            ]

            # Dict of field names and fields (excluding id and version)
            names_fields = {
                name: field_data
                for name, field_data in vars(root_class)["__dataclass_fields__"].items()
                if not is_id_or_version(name)
            }

            # extract (name, class) pairs
            names_classes = []
            for name, field_data in names_fields.items():

                # Find the classes so that we can extract a structure
                if is_class(field_data):
                    # This is an NDM class

                    t = hints[name]
                    args = typing.get_args(t)

                    if args:
                        # Optional (None | X) or list[X]
                        clazz = next(
                            a for a in args if a is not type(None) and a is not list
                        )
                    else:
                        # Plain class, no wrapping
                        clazz = t

                    names_classes.append((name, clazz, is_list(field_data)))

            if "value" in subname_list:
                # names_fields["value"].type.__args__[0] is Decimal
                # this is an "edge" class with a single element

                single_name_class = [
                    (name, clazz)
                    for (name, clazz, is_class) in names_classes
                    if name != "value" and name != "units"
                ]

                single_elem = single_name_class[0][0]

                # collect all lower level keys
                lower_level_kw_list = [
                    get_ccsds_kw_list(clazz) for (name, clazz) in single_name_class
                ]
                flatten_list = [item for subl in lower_level_kw_list for item in subl]
                kw_list.extend(flatten_list)

                # kill the lower level classes
                name_class_sublist: List[_NdmElement] = []
            else:
                # process the class normally

                name_class_sublist = []
                # go one level deeper into the tree and extract subclass info
                for name, clazz, is_list_flag in names_classes:
                    name_class_sublist.append(
                        self._extract_object_submap(
                            name, clazz, root_is_list=is_list_flag
                        )
                    )
                    # print(name_class_sublist[-1])

        else:
            # There is no "__dataclass_fields__"
            name_class_sublist = []
            subname_list = []

        # add all data to object_tree
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
        Identifies the segments in the data, matching with the keywords
        (e.g. "COMMENT" or "ORIGINATOR") for each section.

        The internal object tree is then populated with this information.

        """

        root_ndm_elem = self.object_tree

        max_index, root_min_max = self.__identify_sub_segments(
            root_ndm_elem, self._keys, self._lines
        )
        root_ndm_elem.min_max = root_min_max

        # print(root_ndm_elem)

    def __identify_sub_segments(self, root_ndm_elem, keys, lines, init_index=0):
        """
        Identifies the segments in each branch of object tree recursively,
        matching with the keywords (e.g. "COMMENT" or "ORIGINATOR") for each section.

        The internal object tree is then populated with this information.

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            local root of the object tree
        keys: List[str]
            keys
        lines : List[List[str]] or List[Tuple[str]]
            lines
        init_index : int
            index where the search for limits should start

        Returns
        -------
        (int, _MinMaxTuple)
            Final index of the class and all subclasses
            (should be the starting point of the next search)
            and min, max indices of the `root_ndm_elem`
        """

        # check for prefix
        if root_ndm_elem.clazz.__name__ == "UserDefinedType":
            prefix = "USER_DEFINED"
        else:
            prefix = None

        # check for special types
        if root_ndm_elem.clazz.__name__ in _special_identification_classes:
            # identify segments for special types
            root_min_max = identify_special_sub_segments(
                root_ndm_elem, keys, lines, init_index, prefix
            )
        else:

            # normal processing: identify the root element limits
            root_min_max = get_min_max_indices(
                root_ndm_elem.kw_list,
                init_index,
                keys,
                prefix=prefix,
                single_elem=root_ndm_elem.single_elem,
            )

        # set index to end of keywords
        init_index = root_min_max.max
        max_index = init_index

        if root_ndm_elem.subclass_list:
            # identify sub subsegments
            max_index = self.__identify_sub_sub_segments(
                root_ndm_elem, root_min_max, keys, lines, init_index
            )

        return max_index, root_min_max

    def __identify_sub_sub_segments(
        self, root_ndm_elem, root_min_max, keys, lines, init_index
    ):
        """
        Identify one lower segment (subclasses) of `root_ndm_elem`.

        Parameters
        ----------

        root_ndm_elem : _NdmElement
            local root of the object tree
        root_min_max  : _MinMaxTuple
            min, max indices of the `root_ndm_elem`
        keys: List[str]
            keys
        lines : List[List[str]] or List[Tuple[str]]
            lines
        init_index : int
            index where the search for limits should start

        Returns
        -------
        max_index : int
            Final index of the class and all subclasses
        """

        generated_subclasses: List[_NdmElement] = []
        expected_types = [subclass for subclass in root_ndm_elem.subclass_list]

        max_index = init_index

        for subclass in expected_types:

            if subclass.is_list:
                # process list type subclass (and all subsequent sub-subclasses
                # recursively)
                max_index = self.__identify_list(
                    subclass, keys, lines, init_index, generated_subclasses
                )
                init_index = max_index
            else:
                # Not a list type element, process normally (recursive)
                max_index, subclass_min_max = self.__identify_sub_segments(
                    subclass, keys, lines, init_index
                )
                subclass.min_max = subclass_min_max
                init_index = max_index

                if (
                    subclass.min_max.min == subclass.min_max.max
                    and not subclass.subclass_list
                ):
                    # class returned empty, could be a final level nested class.
                    # Try again from root start point but do not trigger max_point
                    mock_max_index, subclass_min_max = self.__identify_sub_segments(
                        subclass, keys, lines, root_min_max.min
                    )
                    subclass.min_max = subclass_min_max

                # add all generated subclasses
                generated_subclasses.append(subclass)

        # fill the subclasses in the main object with the generated subclasses
        root_ndm_elem.subclass_list = generated_subclasses

        return max_index

    def __identify_list(self, subclass, keys, lines, init_index, generated_subclasses):
        """
        Finds and identifies list type elements.

        Parameters
        ----------
        subclass
        keys: List[str]
            keys
        lines : List[List[str]] or List[Tuple[str]]
            lines
        init_index : int
            index where the search for limits should start
        generated_subclasses : List
            Generated subclass list (to be filled in within the class)

        Returns
        -------
        max_index : int
            Final index of the class and all subclasses

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
        Builds the object processing the data lines and object tree recursively.

        Returns
        -------
        _NdmElement
            Built object tree

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
        Converts the lists to an XML string and fills the corresponding object tree.

        Parameters
        ----------
        root_ndm_elem
            Root element
        full_lines :
            the set of all lines to be used - the object tree uses a subset of this
        parser : XmlParser
            XML Parser

        Returns
        -------
        ndm_object
            NDM object filled with data

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
                    ndm_object = build_ndm_object(root_ndm_elem.clazz, local_lines, prefix)

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
        Builds the special objects, as defined in `_special_processing_classes`.

        Parameters
        ----------
        root_ndm_elem
            Root element
        kw_list
            keyword list
        lines
            lines to be used in object build

        Returns
        -------
        ndm_object
            Populated NDM dataclass instance
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
        """Finds the Attitude Type line within the segment and deletes
        the other options from the subsequent attitude data lines."""

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
        """Build an AttitudeStateType object directly from KVN lines."""

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
    Converts the single element `item_list` to an XML string.
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

