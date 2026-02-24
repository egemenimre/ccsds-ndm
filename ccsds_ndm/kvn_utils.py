# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
Utilities for the KVN File I/O.

"""
import importlib
import inspect
from dataclasses import Field

from ccsds_ndm.mapping import _NdmDataType


def identify_data_type(kvn_source: list[list]) -> _NdmDataType:
    """
    Identify the KVN data type.

    Searches for the string "CCSDS_*_VERS" in the first column.

    Parameters
    ----------
    kvn_source : list[list]
        NDM Data as list of KVN strings

    Returns
    -------
    data_type
        Identified data type

    """
    # Search for "CCSDS_*_VERS" pattern in the first column
    line = next(
        line
        for line in kvn_source
        if len(line) > 1 and line[0].startswith("CCSDS_") and line[0].endswith("_VERS")
    )

    id_str = line[0]
    version_str = line[1]

    return _NdmDataType.find_ndm_type_by_class_id(id_str, version_str)


def is_id_or_version(name: str):
    """
    Checks whether `name` equals to "id" or "version".

    """
    if name == "id" or name == "version":
        return True
    else:
        return False


def is_list(field_data: Field):
    """
    Returns `True` if `field_data.default_factory` is of the type list.
    """
    if field_data.default_factory and field_data.default_factory is list:
        return True
    else:
        return False


def is_class(field_data: Field):
    """
    Checks whether the `field_data` is an NDM class.

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
    # this module name
    module_name = root_class.__bases__[0].__module__

    # some module names are "builtins" due to the way xsdata generates
    # the classes (such as lists), check the base class for correct module

    if module_name == "builtins":
        module_name = root_class.__module__

    # we'll import the module but we have to make sure the class exists there

    # for this_cls_name, this_cls_obj in this_module_classes:

    # try this module and check against its classes
    this_module = importlib.import_module(module_name)
    this_module_classes = inspect.getmembers(this_module, inspect.isclass)

    # Finally, init the correct class
    try:
        clazz = next(cls for name, cls in this_module_classes if name == class_name)
    except StopIteration:
        raise ValueError(f"Class '{class_name}' not found in module '{module_name}'")

    return clazz
