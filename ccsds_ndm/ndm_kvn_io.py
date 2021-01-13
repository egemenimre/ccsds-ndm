# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) 2020 CCSDS-NDM Project Team
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages KVN File I/O.

"""
from collections import namedtuple
from dataclasses import dataclass

from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

from models.ndmxml1 import UserDefinedType

_MinMaxTuple = namedtuple("_MinMaxTuple", ["min", "max"])


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
    min_max: _MinMaxTuple = None


class NdmKvnIo:
    """
    Unified I/O Model for KVN input and output.
    """

    def __init__(self, ndm_class):
        # self.field_list = []
        # self.name_class_dict = {}
        self._init_object_map(ndm_class)

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
        # TODO auto-identify file type

        # parse file to fill lines and keys lists
        self._pre_process_kvn_data(kvn_source)

        # identify the segments
        # self.limits = self._identify_segments()

        self._identify_segments()

        # build the data
        # return self._build_data(self.limits)

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
        root_class : type
            Root class of type Omm, Aem, Cdm etc.

        """

        root_tag = root_class.Meta.name

        self.object_tree = self._extract_object_submap(root_tag, root_class)

        # add id and version keyword info
        self.object_tree.kw_list.extend(["id", "version"])

        # print(self.object_tree)

    def _extract_object_submap(self, root_tag, root_class):
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

        subname_list = [key for key in vars(root_class)["__dataclass_fields__"].keys()]

        names_fields = {
            name: field
            for name, field in vars(root_class)["__dataclass_fields__"].items()
            if not _is_id_or_version(name)
        }

        # extract (name, class) pairs
        names_classes = [
            (name, field.type.__args__[0], _find_occurences(field))
            for name, field in names_fields.items()
            if _is_class(field)
        ]

        name_class_sublist = []
        # go one level deeper into the tree and extract subclass info
        for (name, clazz, n) in names_classes:
            for i in range(n):
                name_class_sublist.append(self._extract_object_submap(name, clazz))
                # print(name_class_sublist[-1])

        # add all data to object_tree
        object_tree = _NdmElement(
            root_tag, root_class, name_class_sublist, kw_list, subname_list
        )

        return object_tree

    def _identify_segments(self):
        """
        Identifies the segments in the data, matching with the keywords
        (e.g. "COMMENT" or "ORIGINATOR") for each section.

        The internal object tree is then populated with this information.

        """

        root_ndm_elem = self.object_tree

        self.__identify_sub_segments(root_ndm_elem)

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

        # identify the root element
        root_ndm_elem.min_max = _get_min_max_indices(
            root_ndm_elem.kw_list, init_index, self._keys, prefix=prefix
        )

        # print(root_ndm_elem.name, root_ndm_elem.min_max)

        # set index to end of keywords
        init_index = root_ndm_elem.min_max.max

        # identify subsegments
        subclass_list = root_ndm_elem.subclass_list
        subclass_list_keys = [subclass.name for subclass in subclass_list]

        max_index = init_index
        for i, name in enumerate(subclass_list_keys):

            subclass = subclass_list[i]
            max_index = self.__identify_sub_segments(subclass, init_index)

            if (
                subclass.min_max.min == subclass.min_max.max
                and not subclass.subclass_list
            ):
                # class returned empty, could be a final level nested class.
                # Try again from root start point but do not trigger max_point
                self.__identify_sub_segments(subclass, root_ndm_elem.min_max.min)

            init_index = max_index

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

        # TODO merge line finding and object generation?
        # init root object
        lines = self._lines[root_ndm_elem.min_max.min : root_ndm_elem.min_max.max]
        kw_list = _get_ccsds_kw_list(root_ndm_elem.clazz)
        if not prefix:
            # intersect list with keywords as a final check
            # protects from wrong keywords on nested structures
            # if prefix is present, then
            lines = [line for line in lines if line[0] in kw_list]

        if not lines and not root_ndm_elem.subclass_list:
            # item has no subclasses and no content, just skip it
            return None

        xml_data = _xmlify_list(root_ndm_elem.name, lines, prefix)
        ndm_object = parser.from_bytes(xml_data, root_ndm_elem.clazz)

        # fill lower level objects
        for subclass in root_ndm_elem.subclass_list:
            subobject = self._build_object_tree(subclass, parser)
            # if subclass.name == "segment":
            #     print(subclass.name)
            if isinstance(getattr(ndm_object, subclass.name), list):
                # this is a list, add the new element
                getattr(ndm_object, subclass.name).append(subobject)
            else:
                # this is not a list, just replace the data
                setattr(ndm_object, subclass.name, subobject)
            # print(subobject.Meta.name)

        return ndm_object


def _find_occurences(field):
    """
    Finds the "min_occurs" string in `field.metadata.keys()` and returns the value.
    Returns 1 if no such field is found.
    """
    n = 1
    if "min_occurs" in field.metadata.keys():
        # add same element if it occurs multiple times
        n = field.metadata["min_occurs"]
    return n


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
    Gets the index belonging to the `key`.

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
    kw_list = [
        var.metadata["name"]
        for var in vars(clazz)["__dataclass_fields__"].values()
        if "name" in var.metadata.keys()
    ]

    # print(kw_list)

    return kw_list


def _get_min_max_indices(tags, start_index, keys, prefix=None):
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

    # find indices of the tags
    index_list = [_get_index(tag, keys, start_index) for tag in tags]

    # remove None values
    index_list = [i for i in index_list if i is not None]

    if len(index_list) == 0:
        # if list is empty, then there are no tags found in data
        return _MinMaxTuple(start_index, start_index)
    else:
        min_of_list = min(index_list)
        # excludes last element, so add one
        max_of_list = max(index_list) + 1
        return _MinMaxTuple(min_of_list, max_of_list)


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
