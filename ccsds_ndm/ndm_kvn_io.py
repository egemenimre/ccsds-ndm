# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2021 Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages KVN File I/O.

"""
from collections import namedtuple
from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List

from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from ccsds_ndm.models.ndmxml2 import (
    Aem,
    AemData,
    AemMetadata,
    AemSegment,
    Apm,
    AttitudeStateType,
    Cdm,
    Ndm,
    Oem,
    OemCovarianceMatrixType,
    OemMetadata,
    Omm,
    Opm,
    QuaternionDerivativeType,
    QuaternionEulerRateType,
    Rdm,
    StateVectorAccType,
    Tdm,
    TdmData,
    TdmMetadata,
    TrackingDataObservationType,
    UserDefinedType,
)
from ccsds_ndm.ndm_xml_io import NdmXmlIo, _is_multi_ndm

_MinMaxTuple = namedtuple("_MinMaxTuple", ["min", "max"])
"""Data structure to keep min and max tuples."""


class _NdmDataType(Enum):
    """
    NDM Data Type (e.g. OEM or AEM).
    """

    AEMv2 = (Aem.id, Aem)
    APMv2 = (Apm.id, Apm)
    CDMv2 = (Cdm.id, Cdm)
    OEMv2 = (Oem.id, Oem)
    OMMv2 = (Omm.id, Omm)
    OPMv2 = (Opm.id, Opm)
    RDMv2 = (Rdm.id, Rdm)
    TDMv2 = (Tdm.id, Tdm)

    def __init__(self, ndm_id, clazz):
        self.clazz = clazz
        self.ndm_id = ndm_id

    @staticmethod
    def find_element(ndm_id):
        """
        Finds the NDM Data Type corresponding to the requested id.

        Parameters
        ----------
        ndm_id : str
            NDM data id (e.g. `aem` or `ndm`)
        Returns
        -------
        ndm_data_type
            correct `_NdmDataType` enum corresponding to the id
        """
        for ndm_data in _NdmDataType:
            if ndm_data.ndm_id == ndm_id:
                return ndm_data


_special_extraction_classes = [AttitudeStateType]

_special_identification_classes = [
    StateVectorAccType,
    OemCovarianceMatrixType,
    AttitudeStateType,
    TrackingDataObservationType,
]
"""List of special classes with special data types in identification.

This lists the NDM special data types that do not conform to the `Key = Value [unit]` format.
"""

_special_processing_classes = [
    StateVectorAccType,
    OemCovarianceMatrixType,
    AemSegment,
    AttitudeStateType,
    TrackingDataObservationType,
]
"""List of special classes with special data types in processing (object build).

This lists the NDM special data types that do not conform to the `Key = Value [unit]` format.
"""

_special_output_header_classes = [
    AemData,
    AemMetadata,
    OemMetadata,
    OemCovarianceMatrixType,
    TdmMetadata,
    TdmData,
]
_special_output_data_classes = [
    StateVectorAccType,
    OemCovarianceMatrixType,
    TrackingDataObservationType,
    AttitudeStateType,
]

_deleted_keywords = {
    Oem: ["META_START", "META_STOP", "COVARIANCE_START", "COVARIANCE_STOP"],
    Aem: ["META_START", "META_STOP", "DATA_START", "DATA_STOP"],
    Tdm: ["META_START", "META_STOP", "DATA_START", "DATA_STOP"],
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
    single_elem: str = None
    min_max: _MinMaxTuple = None
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

    def from_string(self, kvn_source):
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
        ndm_class = _identify_data_type(self._lines)

        # Delete unnecessary keywords if necessary
        if ndm_class in _deleted_keywords.keys():
            deleted_keys = _deleted_keywords.get(ndm_class)
            self._keys = [key for key in self._keys if key not in deleted_keys]
            self._lines = [line for line in self._lines if line[0] not in deleted_keys]

        # Init object map
        self._init_object_map(ndm_class)

        # identify the segments
        self._identify_segments()

        # build the object
        return self._build_object()

    def to_file(self, ndm_obj, kvn_write_file_path):
        """
        Convert and return the given object tree as xml file.

        Parameters
        ----------
        ndm_obj
            input object tree
        kvn_write_file_path : Path
            Path of the XML file to be written
        """
        kvn_write_file_path.write_text(self.to_string(ndm_obj))

    def to_string(self, ndm_obj):
        """
        Convert and return the given object tree as xml string.

        Parameters
        ----------
        ndm_obj
            input object tree

        Returns
        -------
        str
            given object tree as KVN string

        Raises
        ------
        NotImplementedError
            Combined NDM input for KVN not implemented in CCSDS NDM Standard.
        """
        # check for multi-NDM file
        if ndm_obj.Meta.name == Ndm.Meta.name and _is_multi_ndm(ndm_obj):
            raise NotImplementedError(
                "NDM data appears to have more than one data set (e.g. two OPMs). "
                "This sort of NDM output to KVN is not supported. "
                "Try outputting to multiple files instead."
            )

        out_str = [_fill_str_out_kvn(ndm_obj.id, ndm_obj.version)]
        self._collate_str_out("", ndm_obj, out_str)

        # join lines to a single large str
        kvn_string = "\n".join(out_str)

        # print(kvn_string)

        return kvn_string

    def _collate_str_out(self, root_key, root_ndm_obj, out_str):
        """
        Collates the data to build KVN formatted output string from the object.

        Adds lines to `out_str` as more data from the object is extracted.

        Parameters
        ----------
        root_key : str
            key of the root element
        root_ndm_obj
            root NDM object
        out_str : List[str]
            output KVN data as a list of strings

        """

        subclasses = vars(root_ndm_obj)

        if type(root_ndm_obj) in _special_output_data_classes:
            # add special data - can be more than a single line (e.g. stacked covar)
            out_str.extend(
                _collate_special_data_str_out(root_key, root_ndm_obj, out_str)
            )

            # delete all subclasses to cancel lower level processing
            subclasses = {}

        for key, subclass in subclasses.items():
            self._collate_str_out_subclasses(key, subclass, out_str)

        if root_key and "value" not in subclasses.keys() and subclasses:
            out_str.append(_fill_out_single_line(["\n"]))

    def _collate_str_out_subclasses(self, key, ndm_object, out_str):
        """
        Collates the data to build KVN formatted output string from the object.

        Adds lines to `out_str` as more data from the object is extracted.

        Parameters
        ----------
        key : str
            key of the NDM element
        ndm_object
            NDM object
        out_str : List[str]
            output KVN data as a list of strings

        """

        if type(ndm_object) in _special_output_header_classes:
            # add special header
            # out_str.append(_fill_out_single_line(["\n"]))
            out_str.append(_collate_special_header_str_out(ndm_object, is_begin=True))
            out_str.append(_fill_out_single_line(["\n"]))

        if isinstance(ndm_object, (str, int, float)):
            # standard key = value pair
            out_str.append(_fill_str_out_kvn(key, ndm_object))
        elif key == "comment":
            # comment line
            out_str.extend([_fill_str_out_kvn(key, comment) for comment in ndm_object])
        elif (
            getattr(ndm_object, "__dict__", False)
            and ("value" and "units") in vars(ndm_object).keys()
        ):
            # value type with class (e.g. RevType)

            # check the third variable, this might hold the key
            keywords = [
                keyword
                for keyword in vars(ndm_object).keys()
                if keyword not in ["value", "units"]
            ]

            key_used = key
            if keywords:
                key_used = vars(ndm_object)[keywords[0]].value

            if ndm_object.units:
                # with units
                out_str.append(
                    _fill_str_out_kvn(
                        key_used, str(ndm_object.value), ndm_object.units.value
                    )
                )
            else:
                # without units
                out_str.append(_fill_str_out_kvn(key_used, str(ndm_object.value)))
        elif ("value" and "name") in dir(ndm_object):
            # enum type
            out_str.append(_fill_str_out_kvn(key, str(ndm_object.value)))
        elif isinstance(ndm_object, Decimal):
            # just a decimal type
            out_str.append(_fill_str_out_kvn(key, str(ndm_object)))
        elif key == "user_defined":
            # "User defined" line
            out_str.extend(
                [
                    _fill_str_out_kvn(
                        key + "_" + user_def.parameter, user_def.value or ""
                    )
                    for user_def in ndm_object
                ]
            )
        elif isinstance(ndm_object, list):
            # this is a list

            if ndm_object:
                # run only if list has items in it
                if type(ndm_object[0]) in _special_output_header_classes:
                    # add special header
                    out_str.append(_fill_out_single_line(["\n"]))
                    out_str.append(
                        _collate_special_header_str_out(ndm_object[0], is_begin=True)
                    )
                    out_str.append(_fill_out_single_line(["\n"]))

                for subclass_item in ndm_object:
                    self._collate_str_out(key, subclass_item, out_str)

                if type(ndm_object[0]) in _special_output_header_classes:
                    # add special header
                    out_str.append(_fill_out_single_line(["\n"]))
                    out_str.append(
                        _collate_special_header_str_out(ndm_object[0], is_begin=False)
                    )
                    out_str.append(_fill_out_single_line(["\n"]))
        elif ndm_object:
            # this is a class, continue with recursion
            self._collate_str_out(key, ndm_object, out_str)

        if type(ndm_object) in _special_output_header_classes:
            # add special data
            # out_str.append(_fill_out_single_line(["\n"]))
            out_str.append(_collate_special_header_str_out(ndm_object, is_begin=False))
            out_str.append(_fill_out_single_line(["\n"]))

    def _pre_process_kvn_data(self, kvn_source):
        """
        Processes the KVN data string to fill an internal list of key-value pairs.

        Parameters
        ----------
        kvn_source : str
            input string containing KVN data
        """

        input_lines = kvn_source.split("\n")

        lines = []
        for line in input_lines:
            # strip spaces around the line
            line = line.strip()
            # skip empty lines
            if not line.strip():
                continue

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
        lines[0] = ["id", lines[0][0]]
        lines[1][0] = "version"

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

    def _extract_object_submap(self, root_tag, root_class, root_is_list=False):
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
        kw_list = [kw for kw in _get_ccsds_kw_list(root_class) if kw.isupper()]

        single_elem = None
        if "__dataclass_fields__" in vars(root_class).keys():
            # fill requisite data to populate the NdmElement
            subname_list = [
                key for key in vars(root_class)["__dataclass_fields__"].keys()
            ]

            names_fields = {
                name: field_name
                for name, field_name in vars(root_class)["__dataclass_fields__"].items()
                if not _is_id_or_version(name)
            }

            # extract (name, class) pairs
            names_classes = [
                (name, field_name.type.__args__[0], _is_list(field_name))
                for name, field_name in names_fields.items()
                if _is_class(field_name)
            ]

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
                    _get_ccsds_kw_list(clazz) for (name, clazz) in single_name_class
                ]
                flatten_list = [item for subl in lower_level_kw_list for item in subl]
                kw_list.extend(flatten_list)

                # kill the lower level classes
                name_class_sublist: List[_NdmElement] = []
            else:
                name_class_sublist = []
                # go one level deeper into the tree and extract subclass info
                for (name, clazz, is_list) in names_classes:
                    name_class_sublist.append(
                        self._extract_object_submap(name, clazz, root_is_list=is_list)
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
        if root_ndm_elem.clazz == UserDefinedType:
            prefix = "USER_DEFINED"
        else:
            prefix = None

        # check for special types
        if root_ndm_elem.clazz in _special_identification_classes:
            # identify segments for special types
            root_min_max = _identify_special_sub_segments(
                root_ndm_elem, keys, lines, init_index, prefix
            )
        else:

            # normal processing: identify the root element limits
            root_min_max = _get_min_max_indices(
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
            elif subclass_min_max.min > last_max_index:
                # There is some gap in data,
                # try other classes to process the data in between
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
        # prepare parser
        parser = XmlParser(config=ParserConfig(fail_on_unknown_properties=True))

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
        if root_ndm_elem.clazz == UserDefinedType:
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
            if root_ndm_elem.clazz in _special_processing_classes:
                xml_data = self.__build_special_objects(
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

                if kw_list == ["id", "version"]:
                    # Process as outermost element
                    xml_data = _xmlify_root(root_ndm_elem.clazz.Meta.name, local_lines)

                elif root_ndm_elem.single_elem:
                    # Process as single element
                    xml_data = _xmlify_single_elem(
                        root_ndm_elem.name, local_lines, root_ndm_elem.single_elem
                    )
                else:
                    # process normally (with or without prefix)
                    xml_data = _xmlify_list(root_ndm_elem.name, local_lines, prefix)

        ndm_object = parser.from_bytes(xml_data, root_ndm_elem.clazz)

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
        xml_data
            Binary XML output of the object
        """

        if root_ndm_elem.clazz is AemSegment:
            # This is the AEM segment data type

            # process subclasses
            self.__prepare_aemsegment_sub_objects(root_ndm_elem)

            # proceed normally for the class itself
            xml_data = _xmlify_list(root_ndm_elem.name, lines)

        elif root_ndm_elem.clazz is AttitudeStateType:
            # This is the AttitudeStateType data type
            xml_data = self.__xmlify_att_segment_data(root_ndm_elem, lines)

        elif root_ndm_elem.clazz is StateVectorAccType:
            # parse StateVectorAccType type data
            synth_lines = list(zip(kw_list, lines[0][0].split()))
            xml_data = _xmlify_list(root_ndm_elem.name, synth_lines)

        elif root_ndm_elem.clazz is OemCovarianceMatrixType:
            # Stacked covariance data
            datalines = [line[0].split() for line in lines if not line[0].isalpha()]
            kvnlines = [line for line in lines if line[0].isalpha()]
            # flatten the list
            data_list = [item for sublist in datalines for item in sublist]
            synth_lines = list(zip(kw_list[3:], data_list))
            kvnlines.extend(synth_lines)
            xml_data = _xmlify_list(root_ndm_elem.name, kvnlines)

        elif root_ndm_elem.clazz is TrackingDataObservationType:
            # Tracking data, parse the single line
            synth_lines = list(zip(["EPOCH", lines[0][0]], lines[0][1].split()))
            xml_data = _xmlify_list(root_ndm_elem.name, synth_lines)

        else:
            raise ValueError(
                f"Unknown Special Data Type ({root_ndm_elem.clazz}) encountered "
                f"while building object."
            )

        return xml_data

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

    def __xmlify_att_segment_data(self, root_ndm_elem, lines):
        """Convert AttitudeSegmentType data to XML."""

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

        att_state_obj = AttitudeStateType()
        setattr(att_state_obj, root_ndm_elem.subclass_list[0].name, internal_obj)
        xml_data = NdmXmlIo().to_string(att_state_obj)

        # delete id line and delete "Type" from tags
        xml_data = xml_data[xml_data.index("\n") + 1 :]
        xml_data = xml_data.replace("Type", "")

        # convert to binary
        xml_data = xml_data.encode()
        # kill the subclasses, they are already processed
        root_ndm_elem.subclass_list = []
        root_ndm_elem.subname_list = []

        return xml_data


def _identify_data_type(kvn_source):
    """
    Identify the KVN data type.

    Parameters
    ----------
    kvn_source : list[list]
        NDM Data as list of KVN strings

    Returns
    -------
    data_type
        Identified data type

    """
    # Use the id: "CCSDS_CDM_VERS"
    data_type = _NdmDataType.find_element(kvn_source[0][1]).clazz
    return data_type


def _identify_special_sub_segments(root_ndm_elem, keys, lines, init_index, prefix=None):
    """Identifies the segments of the special objects, as defined in
    `_special_identification_classes`.

    Parameters
    ----------
    root_ndm_elem : _NdmElement
        local root of the object tree
    keys: List[str]
        keys
    lines : List[List[str]]
        lines
    init_index : int
        index where the search for limits should start
    prefix : str
        Prefix (e.g. "USER_DEFINED")

    Returns
    -------
    root_min_max : _MinMaxTuple
        Min max limits of the element
    """
    if (
        root_ndm_elem.clazz is StateVectorAccType
        or root_ndm_elem.clazz is AttitudeStateType
    ):
        # Epoch start and columns of data

        # is this a valid date string? take the first element
        datestr = lines[init_index][0].split()[0]

        # # get rid of anything beyond seconds (high precision messes up datetime parser)
        # datestr = datestr.split(".")[0]
        # datetime.fromisoformat(datestr)

        # can be of format "2007-075T16:50:01" or normal ISO string
        if datestr[:4].isnumeric() and datestr[4] == "-":
            root_min_max = _MinMaxTuple(init_index, init_index + 1)
        else:
            # line is not of correct type, just skip it
            root_min_max = _MinMaxTuple(init_index, init_index)

        return root_min_max

    elif root_ndm_elem.clazz is TrackingDataObservationType:

        # is this a valid date string? take the first element
        datestr = lines[init_index][1].split()[0]

        # can be of format "2007-075T16:50:01" or normal ISO string
        if datestr[:4].isnumeric() and datestr[4] == "-":
            root_min_max = _MinMaxTuple(init_index, init_index + 1)
        else:
            # line is not of correct type, just skip it
            root_min_max = _MinMaxTuple(init_index, init_index)

        return root_min_max

    elif root_ndm_elem.clazz is OemCovarianceMatrixType:
        # Stacked covariance data

        # identify the root element limits
        temp_min_max = _get_min_max_indices(
            root_ndm_elem.kw_list,
            init_index,
            keys,
            prefix=prefix,
            single_elem=root_ndm_elem.single_elem,
        )

        if temp_min_max.min == temp_min_max.max:
            # No valid type, just skip it
            root_min_max = _MinMaxTuple(init_index, init_index)
        else:
            found_data = True
            i = temp_min_max.max
            while found_data:
                try:
                    float(lines[i][0].split()[0])
                    i += 1
                except (ValueError, IndexError):
                    found_data = False

            root_min_max = _MinMaxTuple(temp_min_max.min, i)

        return root_min_max

    else:
        raise ValueError(
            f"Unknown Special Data Type ({root_ndm_elem.clazz}) encountered "
            f"while identifying segments."
        )


def _is_list(field_name):
    """
    Returns `True` if `field_name.default_factory` is of the type list.
    """
    if field_name.default_factory and field_name.default_factory is list:
        return True
    else:
        return False


def _is_id_or_version(name):
    """
    Checks whether `name` equals to "id" or "version".

    """
    if name == "id" or name == "version":
        return True
    else:
        return False


def _is_class(field_name):
    """
    Checks whether the `field_name` is an NDM class.

    """
    if "name" in field_name.metadata.keys():
        # can be a tag or low level class
        if field_name.metadata["name"].isupper():
            return False
        else:
            return True
    return True


def _get_index(key, keys, *args):
    """
    Gets the first index belonging to the `key`.

    Parameters
    ----------
    key : str
        Key value (e.g. "CREATION_DATE")
    keys : list[str]
        List of keys
    args
        Additional arguments to be fed to `index` method of `list` (e.g. start index)

    Returns
    -------
    index : int or None
        Index of the `key` in the list `keys`, `None` if key is not found

    """
    try:
        return keys.index(key, *args)
    except ValueError:
        pass


def _get_ccsds_kw_list(clazz):
    """
    Extracts and returns the keyword list from the class `clazz`.
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


def __process_comment_lines(tags, start_index, keys, index_list):
    """
    Process comments with the following algorithm:
        1. If there are no COMMENT tags in the class, skip processing
        2. If there is only COMMENT tag in the class, add a single line of comment,
           if available (indicates a container type class like data or metadata)
        3. If all tags are empty, skip processing; the comments likely belong to another
           block later on in the file
        4. If some tags are filled, add all comments between `start_index` and
           `max(index_list)`
    """
    if "COMMENT" in tags:
        if len(tags) == 1:
            # no tags, this is a header sort of class, claim just one COMMENT tag, if available
            if keys[start_index] == "COMMENT":
                index_list.extend([start_index])

        elif len(index_list) > 0:
            # some data is available, claim all comments between start_index and max_index
            # excludes last element, so add one
            max_of_list = max(index_list) + 1
            comment_indexes = [
                idx
                for idx, key in enumerate(
                    keys[start_index:max_of_list], start=start_index
                )
                if keys[idx] == "COMMENT"
            ]
            index_list.extend(comment_indexes)


def _get_min_max_indices(tags, start_index, keys, prefix=None, single_elem=None):
    """
    Gets the min/max indices of the section.

    This matches the tags of a section with the actual tags found in the data and finds
    where the section begins and ends in the data.
    """
    new_keys = []
    if prefix:
        for key in keys[start_index:]:
            if key.startswith(prefix):
                new_keys.append(key)
        tags.extend(new_keys)

    # find indices of the tags - except for comments
    index_named_list = [
        [tag, _get_index(tag, keys, start_index)] for tag in tags if tag != "COMMENT"
    ]

    # remove None values
    index_list = [
        index_name[1] for index_name in index_named_list if index_name[1] is not None
    ]

    # add all comment lines
    __process_comment_lines(tags, start_index, keys, index_list)

    # check for non-consecutive data and chop them if necessary
    if index_list:
        # list isn't empty
        index_list.sort()
        ideal_list = list(range(min(index_list), max(index_list) + 1))
        diff_list = [n for n in ideal_list if n not in index_list]
        # if diff_list has any data, this is not good. Either this is a nested class
        # or it has numerical data in between (which is separated by spaces).
        # If latter case holds, delete the numerical data and the rest.
        if diff_list:
            containing_spaces = any(" " in keys[n] for n in diff_list)

            # find repeating data
            diff_list_keys = [keys[i] for i in diff_list]
            diff_set_keys = set(diff_list_keys)
            repeating_data = len(diff_list_keys) != len(diff_set_keys)

            if containing_spaces or repeating_data:
                # there are no keys in between, all numerical data
                # chop list to consecutive elements only
                index_list = [
                    n
                    for i, n in enumerate(index_list)
                    if index_list[i] == ideal_list[i]
                ]

    if not index_list:
        # list is empty, there are no tags found in data
        return _MinMaxTuple(start_index, start_index)
    else:
        min_of_list = min(index_list)
        if single_elem:
            # This is a single element item, just take the first one
            max_of_list = min_of_list + 1
        else:
            # excludes last element, so add one
            max_of_list = max(index_list) + 1
        return _MinMaxTuple(min_of_list, max_of_list)


def _xmlify_root(root_tag, item_list):
    """Converts the outermost root to and XML string"""

    # create XML
    root = etree.Element(root_tag)

    for item in item_list:
        root.attrib[item[0]] = item[1]

    return etree.tostring(root, pretty_print=True)


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


def _xmlify_list(root_tag, item_list, prefix=None):
    """
    Converts the `item_list` to an XML string.
    """
    # create XML
    root = etree.Element(root_tag)

    if prefix:
        for item in item_list:
            child = etree.Element(prefix)
            child.attrib["parameter"] = item[0].replace(prefix + "_", "")
            child.text = item[1]
            root.append(child)
    else:
        for item in item_list:
            child = etree.Element(item[0])
            if len(item) > 2:
                # add units if available
                child.attrib["units"] = item[2]
            child.text = item[1]
            root.append(child)

    return etree.tostring(root, pretty_print=True)


def _fill_str_out_kvn(key, value, unit=None):
    """
    Fills a line in standard 'key = value' pair or 'key = value [unit]' triplet format.

    Parameters
    ----------
    key : str
        key
    value : str
        value
    unit : str or None
        unit (if available)

    Returns
    -------
    str
        'key = value' pair or 'key = value [unit]' triplet

    """
    if unit:
        # standard 'key = value [unit]' triplet
        new_line = f"{key.upper():<20} = {str(value):<18}[{unit}]"
    else:
        # standard 'key = value' pair or similar (e.g. comment)
        new_line = f"{key.upper():<20} = {str(value)}"

    return new_line


def _fill_str_out_multi_kvn(key, value1, value2):
    """
    Fills a line in standard 'key = value value' triplet format.

    Parameters
    ----------
    key : str
        key
    value1 : str
        value 1
    value2 : str
        value 2

    Returns
    -------
    str
        'key = value value' triplet

    """

    # standard 'key = value' pair or similar (e.g. comment)
    new_line = f"{key.upper():<20} = {str(value1):<30}{str(value2)} "

    return new_line


def _fill_out_single_line(line):
    """
    Flattens the elements in the line to form a single string with data separated
    with spaces.

    Parameters
    ----------
    line : List[str]
        line with string

    Returns
    -------
    str
        "" if line[0] == "\n", else the elements of the line flattened
        with space as delimiter

    """
    if line[0] == "\n":
        # section break
        return ""
    else:
        return "  ".join(line)


def _collate_special_header_str_out(ndm_object, is_begin=True):
    """
    Writes the special headers (e.g. `META_START`, `COVARIANCE_STOP` )

    Parameters
    ----------
    ndm_object
        NDM object
    is_begin : bool
        true if it is a header at the beginning, false if a header at the end

    Returns
    -------
    str
        KVN line

    """
    if type(ndm_object) in [AemMetadata, OemMetadata, TdmMetadata]:
        if is_begin:
            return _fill_out_single_line(["META_START"])
        else:
            return _fill_out_single_line(["META_STOP"])

    if type(ndm_object) in [AemData, TdmData]:
        if is_begin:
            return _fill_out_single_line(["DATA_START"])
        else:
            return _fill_out_single_line(["DATA_STOP"])

    if type(ndm_object) is OemCovarianceMatrixType:
        if is_begin:
            return _fill_out_single_line(["COVARIANCE_START"])
        else:
            return _fill_out_single_line(["COVARIANCE_STOP"])


def _collate_special_data_str_out(key, ndm_obj, out_str):
    """
    Converts the special data into their KVN equivalent line.

    Parameters
    ----------
    key : str
        key
    ndm_obj
        NDM object
    out_str : List[str]
        output KVN data as a list of strings


    Returns
    -------
    List[str]
        single element list with the line
    """

    if type(ndm_obj) is StateVectorAccType:
        # fill all elements ("value" if something like PositionType or just its str value)
        line = [
            str(getattr(elem, "value", elem)) for elem in vars(ndm_obj).values() if elem
        ]
        return [_fill_out_single_line(line)]

    if type(ndm_obj) is AttitudeStateType:
        # find element with valid data
        att_obj = [att for att in vars(ndm_obj).values() if att]

        if att_obj:
            quaternion = True if str(att_obj[0]).startswith("Quaternion") else False

            # extract rot objects
            rot_objects = [
                vars(rot_obj)
                for att_key, rot_obj in vars(att_obj[0]).items()
                if att_key != "epoch"
            ]
            if quaternion:
                # process with quaternion, order is important

                # find quaternion type line (start from the end)
                quat_type = next(
                    x for x in reversed(out_str) if x.startswith("QUATERNION_TYPE")
                ).split("=")[-1]

                quat_last = True if quat_type.strip().startswith("LAST") else False

                if quat_last:
                    line = [
                        str(rot_objects[0]["q1"]),
                        str(rot_objects[0]["q2"]),
                        str(rot_objects[0]["q3"]),
                        str(rot_objects[0]["qc"]),
                    ]
                else:
                    line = [
                        str(rot_objects[0]["qc"]),
                        str(rot_objects[0]["q1"]),
                        str(rot_objects[0]["q2"]),
                        str(rot_objects[0]["q3"]),
                    ]

                if isinstance(att_obj[0], QuaternionEulerRateType):
                    line.extend(
                        [
                            str(rot_objects[1]["rotation1"].value),
                            str(rot_objects[1]["rotation2"].value),
                            str(rot_objects[1]["rotation3"].value),
                        ]
                    )
                elif isinstance(att_obj[0], QuaternionDerivativeType):
                    if quat_last:
                        line.extend(
                            [
                                str(rot_objects[0]["q1_dot"]),
                                str(rot_objects[0]["q2_dot"]),
                                str(rot_objects[0]["q3_dot"]),
                                str(rot_objects[0]["qc_dot"]),
                            ]
                        )
                    else:
                        line.extend(
                            [
                                str(rot_objects[0]["qc_dot"]),
                                str(rot_objects[0]["q1_dot"]),
                                str(rot_objects[0]["q2_dot"]),
                                str(rot_objects[0]["q3_dot"]),
                            ]
                        )
            else:
                # process normally - extract values from the rot objects
                line = [
                    str(getattr(elem, "value", elem))
                    for rot_obj in rot_objects
                    for elem in rot_obj.values()
                ]

            # add epoch to the beginning
            line.insert(0, vars(att_obj[0])["epoch"])
            return [_fill_out_single_line(line)]

    if type(ndm_obj) is TrackingDataObservationType:
        # find element with data

        item_key, item_value = [
            (k, v)
            for k, v in vars(ndm_obj).items()
            if isinstance(v, Decimal) and k != "epoch"
        ][0]

        return [
            _fill_str_out_multi_kvn(item_key, vars(ndm_obj)["epoch"], str(item_value))
        ]

    if type(ndm_obj) is OemCovarianceMatrixType:
        lines = []
        # comment line
        lines.extend([_fill_str_out_kvn(key, comment) for comment in ndm_obj.comment])

        lines.append(_fill_str_out_kvn("epoch", ndm_obj.epoch))

        if ndm_obj.cov_ref_frame:
            lines.append(_fill_str_out_kvn("cov_ref_frame", ndm_obj.cov_ref_frame))

        max_elems = 1
        covar_data_iter = iter(
            [
                getattr(elem, "value")
                for elem in vars(ndm_obj).values()
                if hasattr(elem, "value")
            ]
        )
        while True:
            try:
                lines.append(
                    _fill_out_single_line(
                        [str(next(covar_data_iter)) for i in range(max_elems)]
                    )
                )
                max_elems += 1
            except StopIteration:
                break

        return lines
