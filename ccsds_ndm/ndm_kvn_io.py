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
from enum import Enum
from typing import List

from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from ccsds_ndm.models.ndmxml1 import (
    Aem,
    Apm,
    Cdm,
    Oem,
    Omm,
    Opm,
    Rdm,
    Tdm,
    UserDefinedType,
)

_MinMaxTuple = namedtuple("_MinMaxTuple", ["min", "max"])


class _NdmDataType(Enum):
    """
    NDM Data Type (e.g. OEM or AEM).
    """

    AEMv1 = (Aem.id, Aem)
    APMv1 = (Apm.id, Apm)
    CDMv1 = (Cdm.id, Cdm)
    OEMv1 = (Oem.id, Oem)
    OMMv1 = (Omm.id, Omm)
    OPMv1 = (Opm.id, Opm)
    RDMv1 = (Rdm.id, Rdm)
    TDMv1 = (Tdm.id, Tdm)

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


class NdmKvnIo:
    """
    Unified I/O Model for KVN input and output.
    """

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

        # print(self.object_tree)

    def _extract_object_submap(self, root_tag, root_class, root_is_list=False):
        """
        Extracts the object submap and all elements in the tree recursively.

        Parameters
        ----------
        root_tag : str
            Variable name of the root class ("omm", "aem", "cdm" etc.)
        root_class : type
            Root class of type Omm, Aem, Cdm etc.

        Returns
        -------
        _NdmElement
            NDM object tree

        """
        kw_list = [kw for kw in _get_ccsds_kw_list(root_class) if kw.isupper()]

        single_elem = None
        if "__dataclass_fields__" in vars(root_class).keys():
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
        Final index (should be the starting point of the next search)
        """

        # check for prefix
        if root_ndm_elem.clazz == UserDefinedType:
            prefix = "USER_DEFINED"
        else:
            prefix = None

        # identify the root element limits
        root_min_max = _get_min_max_indices(
            root_ndm_elem.kw_list,
            init_index,
            self._keys,
            prefix=prefix,
            single_elem=root_ndm_elem.single_elem,
        )

        # set index to end of keywords
        init_index = root_min_max.max

        # identify subsegments
        subclass_list = root_ndm_elem.subclass_list
        subclass_list_keys = [subclass.name for subclass in subclass_list]

        max_index = init_index
        for i, name in enumerate(subclass_list_keys):

            subclass = subclass_list[i]

            if subclass.is_list:
                # This is a list type element, loop until all elements are collected
                max_index, subclass_min_max = self.__identify_sub_segments(
                    subclass, init_index
                )
                subclass.min_max = subclass_min_max
                init_index = max_index

                if max_index >= len(self._lines):
                    # End of file reached
                    continue

                # try another run with a copy of the subclass
                # (to prevent changes in subclasses)
                temp_max_index, temp_subclass_min_max = self.__identify_sub_segments(
                    deepcopy(subclass), init_index
                )

                # if temp_subclass_min_max.min == temp_subclass_min_max.max:
                if temp_max_index == max_index:
                    # There is probably no more data
                    break
                else:
                    # inject another element
                    new_subclass = deepcopy(subclass)
                    subclass_list.insert(i + 1, new_subclass)
                    subclass_list_keys.insert(i + 1, name)

            else:
                max_index, subclass_min_max = self.__identify_sub_segments(
                    subclass, init_index
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

        return max_index, root_min_max

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
        ndm_object = self._build_object_tree(root_ndm_elem, parser)

        return ndm_object

    def _build_object_tree(self, root_ndm_elem, parser):
        """
        Converts the lists to an XML string and fills the corresponding object tree.

        """
        # check for prefix
        if root_ndm_elem.clazz == UserDefinedType:
            prefix = "USER_DEFINED"
        else:
            prefix = None

        # init root object
        lines = self._lines[root_ndm_elem.min_max.min : root_ndm_elem.min_max.max]
        # kw_list = _get_ccsds_kw_list(root_ndm_elem.clazz)
        kw_list = root_ndm_elem.kw_list
        if not prefix:
            # intersect list with keywords as a final check
            # protects from wrong keywords on nested structures
            # if prefix is present, then
            lines = [line for line in lines if line[0] in kw_list]

        if not lines and not root_ndm_elem.subclass_list:
            # item has no subclasses and no content, just skip it
            return None

        if root_ndm_elem.single_elem:
            xml_data = _xmlify_single_elem(
                root_ndm_elem.name, lines, root_ndm_elem.single_elem
            )
        else:
            xml_data = _xmlify_list(root_ndm_elem.name, lines, prefix)
        ndm_object = parser.from_bytes(xml_data, root_ndm_elem.clazz)

        # fill lower level objects
        for subclass in root_ndm_elem.subclass_list:
            subobject = self._build_object_tree(subclass, parser)
            # if subclass.name == "segment":
            #     print(subclass.name)
            if isinstance(getattr(ndm_object, subclass.name), list):
                if subobject:
                    # this is a list, add the new element
                    getattr(ndm_object, subclass.name).append(subobject)
            else:
                # this is not a list, just replace the data
                setattr(ndm_object, subclass.name, subobject)
            # print(subobject.id)

        return ndm_object


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
