# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 CCSDS-NDM Project Team
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages KVN File I/O.

"""
from collections import namedtuple
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import List

from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from ccsds_ndm.models.ndmxml2 import (
    Aem,
    Apm,
    Cdm,
    Oem,
    OemCovarianceMatrixType,
    Omm,
    Opm,
    Rdm,
    StateVectorAccType,
    Tdm,
    UserDefinedType,
)

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


class _SpecialDataTypes(Enum):
    """
    Tags for NDM special data types that do not conform to the `Key = Value [unit]` format.
    """

    EPOCHSTARTNUMCOLS = auto()
    """ Numerical values in columns with the first value as a date."""
    STACKEDCOVAR = auto()
    """ Stacked covariance matrix."""


_special_classes = {
    StateVectorAccType: _SpecialDataTypes.EPOCHSTARTNUMCOLS,
    OemCovarianceMatrixType: _SpecialDataTypes.STACKEDCOVAR,
}
"""Dict of special classes with special data types.

This lists the NDM special data types that do not conform to the `Key = Value [unit]` format.
"""


_deleted_keywords = {
    Oem: ["META_START", "META_STOP", "COVARIANCE_START", "COVARIANCE_STOP"]
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
    special_type: _SpecialDataTypes = None


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
        """
        raise NotImplementedError("This functionality is not implemented yet.")

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
                name: field
                for name, field in vars(root_class)["__dataclass_fields__"].items()
                if not _is_id_or_version(name)
            }

            # extract (name, class) pairs
            names_classes = [
                (name, field.type.__args__[0], _is_list(field))
                for name, field in names_fields.items()
                if _is_class(field)
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
            special_type=_special_classes.get(root_class, None),
        )

        return object_tree

    def _identify_segments(self):
        """
        Identifies the segments in the data, matching with the keywords
        (e.g. "COMMENT" or "ORIGINATOR") for each section.

        The internal object tree is then populated with this information.

        """

        root_ndm_elem = self.object_tree

        max_index, root_min_max = self.__identify_sub_segments(root_ndm_elem)
        root_ndm_elem.min_max = root_min_max

        # print(root_ndm_elem)

    def __identify_sub_segments(self, root_ndm_elem, init_index=0):
        """
        Identifies the segments in each branch of object tree recursively,
        matching with the keywords (e.g. "COMMENT" or "ORIGINATOR") for each section.

        The internal object tree is then populated with this information.

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            local root of the object tree
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
        if root_ndm_elem.special_type:
            # identify segments for special types
            root_min_max = self.__identify_special_sub_segments(
                root_ndm_elem, init_index, prefix
            )
        else:
            # normal processing: identify the root element limits
            root_min_max = _get_min_max_indices(
                root_ndm_elem.kw_list,
                init_index,
                self._keys,
                prefix=prefix,
                single_elem=root_ndm_elem.single_elem,
            )

        # set index to end of keywords
        init_index = root_min_max.max
        max_index = init_index

        if root_ndm_elem.subclass_list:
            # identify sub subsegments
            max_index = self.__identify_sub_sub_segments(
                root_ndm_elem, root_min_max, init_index
            )

        return max_index, root_min_max

    def __identify_sub_sub_segments(self, root_ndm_elem, root_min_max, init_index):
        """
        Identify one lower segment (subclasses) of `root_ndm_elem`.

        Parameters
        ----------

        root_ndm_elem : _NdmElement
            local root of the object tree
        root_min_max  : _MinMaxTuple
            min, max indices of the `root_ndm_elem`
        init_index : int
            index where the search for limits should start

        Returns
        -------
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
                    subclass, init_index, generated_subclasses
                )
                init_index = max_index
            else:
                # Not a list type element, process normally (recursive)
                max_index, subclass_min_max = self.__identify_sub_segments(
                    subclass,
                    init_index,
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
                        subclass, root_min_max.min
                    )
                    subclass.min_max = subclass_min_max

                # add all generated subclasses
                generated_subclasses.append(subclass)

        # fill the subclasses in the main object with the generated subclasses
        root_ndm_elem.subclass_list = generated_subclasses

        return max_index

    def __identify_list(self, subclass, init_index, generated_subclasses):
        """
        Finds and identifies list type elements.

        Parameters
        ----------
        subclass
        init_index
        generated_subclasses : List
            Generated subclass list (to be filled in within the class)

        Returns
        -------
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
                clean_obj, init_index
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

                if max_index >= len(self._lines):
                    # End of file reached, stop the while loop
                    has_elements = False

        # insert resulting list into expected subclasses
        generated_subclasses.extend(subclass_list)

        return max_index

    def __identify_special_sub_segments(self, root_ndm_elem, init_index, prefix=None):
        """Identifies the segments of the special objects, as defined in
        `_SpecialDataTypes`.

        Parameters
        ----------
        root_ndm_elem : _NdmElement
            local root of the object tree
        init_index : int
            index where the search for limits should start
        prefix : str
            Prefix (e.g. "USER_DEFINED")

        Returns
        -------
        root_min_max : _MinMaxTuple
            Min max limits of the element
        """
        if root_ndm_elem.special_type is _SpecialDataTypes.EPOCHSTARTNUMCOLS:
            # Epoch start and columns of data
            try:
                # is this a valid date string? take the first element
                datestr = self._lines[init_index][0].split()[0]
                # get rid of anything beyond seconds (high precision messes up datetime parser)
                datestr = datestr.split(".")[0]
                datetime.fromisoformat(datestr)
                root_min_max = _MinMaxTuple(init_index, init_index + 1)
            except ValueError:
                # line is not of correct type, just skip it
                root_min_max = _MinMaxTuple(init_index, init_index)

            return root_min_max

        elif root_ndm_elem.special_type is _SpecialDataTypes.STACKEDCOVAR:
            # Stacked covariance data

            # identify the root element limits
            temp_min_max = _get_min_max_indices(
                root_ndm_elem.kw_list,
                init_index,
                self._keys,
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
                        float(self._lines[i][0].split()[0])
                        i += 1
                    except (ValueError, IndexError):
                        found_data = False

                root_min_max = _MinMaxTuple(temp_min_max.min, i)

            return root_min_max
        else:
            raise ValueError(
                f"Unknown Special Data Type ({root_ndm_elem.special_type}) encountered "
                f"while identifying segments."
            )

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
        ndm_object = self.__build_object_tree(root_ndm_elem, parser)

        return ndm_object

    def __build_object_tree(self, root_ndm_elem, parser):
        """
        Converts the lists to an XML string and fills the corresponding object tree.

        Parameters
        ----------
        root_ndm_elem
            Root element
        parser : XmlParser
            XML Parser

        Returns
        -------
        NDM object filled with data

        """
        # check for prefix
        if root_ndm_elem.clazz == UserDefinedType:
            prefix = "USER_DEFINED"
        else:
            prefix = None

        # init root object
        lines = self._lines[root_ndm_elem.min_max.min : root_ndm_elem.min_max.max]
        kw_list = root_ndm_elem.kw_list

        if not lines and not root_ndm_elem.subclass_list:
            # item has no subclasses and no content, just skip it
            return None
        else:
            # check for special types
            if root_ndm_elem.special_type:
                xml_data = _build_special_objects(root_ndm_elem, kw_list, lines)
            else:
                # not a special type, proceed normally
                if not prefix:
                    # intersect list with keywords as a final check
                    # protects from wrong keywords on nested structures
                    # if prefix is present, then
                    lines = [line for line in lines if line[0] in kw_list]

                if not lines and not root_ndm_elem.subclass_list:
                    # item has no subclasses and no content, just skip it
                    return None

                if root_ndm_elem.single_elem:
                    # Process as single element
                    xml_data = _xmlify_single_elem(
                        root_ndm_elem.name, lines, root_ndm_elem.single_elem
                    )
                else:
                    # process normally (with or without prefix)
                    xml_data = _xmlify_list(root_ndm_elem.name, lines, prefix)

        ndm_object = parser.from_bytes(xml_data, root_ndm_elem.clazz)

        # print(root_ndm_elem.name)

        # fill lower level objects
        for subclass in root_ndm_elem.subclass_list:
            subobject = self.__build_object_tree(subclass, parser)
            if isinstance(getattr(ndm_object, subclass.name), list):
                if subobject:
                    # this is a list, add the new element
                    getattr(ndm_object, subclass.name).append(subobject)
            else:
                # this is not a list, just replace the data
                setattr(ndm_object, subclass.name, subobject)

        return ndm_object


def _build_special_objects(root_ndm_elem, kw_list, lines):
    """Builds the special objects, as defined in `_SpecialDataTypes`."""

    if root_ndm_elem.special_type is _SpecialDataTypes.EPOCHSTARTNUMCOLS:
        # parse Epoch Start Num Cols type data
        synth_lines = list(zip(kw_list, lines[0][0].split()))
        xml_data = _xmlify_list(root_ndm_elem.name, synth_lines)

    elif root_ndm_elem.special_type is _SpecialDataTypes.STACKEDCOVAR:
        # Stacked covariance data
        datalines = [line[0].split() for line in lines if not line[0].isalpha()]
        kvnlines = [line for line in lines if line[0].isalpha()]
        # flatten the list
        data_list = [item for sublist in datalines for item in sublist]
        synth_lines = list(zip(kw_list[3:], data_list))
        kvnlines.extend(synth_lines)
        xml_data = _xmlify_list(root_ndm_elem.name, kvnlines)

    else:
        raise ValueError(
            f"Unknown Special Data Type ({root_ndm_elem.special_type}) encountered "
            f"while building object."
        )

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


def _is_list(field):
    """
    Returns `True` if `field.default_factory` is of the type list.
    """
    if field.default_factory and field.default_factory is list:
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


def _is_class(field):
    """
    Checks whether the `field` is an NDM class.

    """
    if "name" in field.metadata.keys():
        # can be a tag or low level class
        if field.metadata["name"].isupper():
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

    if len(index_list) == 0:
        # if list is empty, then there are no tags found in data
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
