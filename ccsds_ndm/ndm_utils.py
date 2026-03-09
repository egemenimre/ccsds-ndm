# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages NDM Class Utilities.

"""

import dataclasses


def is_combi_ndm(ndm_obj) -> bool:
    """Returns True if *ndm_obj* is a combined NDM container (Meta.name == 'ndm')."""
    return getattr(getattr(ndm_obj, "Meta", None), "name", None) == "ndm"


def is_multi_ndm(ndm_obj) -> bool:
    """Returns True if the NDM container holds more than one dataset.

    This directly returns False if the ``ndm_obj`` is not a combined NDM container.
    """
    if not is_combi_ndm(ndm_obj):
        return False
    total = sum(
        len(v)
        for f in dataclasses.fields(ndm_obj)
        if isinstance((v := getattr(ndm_obj, f.name)), list)
    )
    return total > 1
