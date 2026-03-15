# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
KVN registry package.

Sentinels, ``TypeHandler``, and ``DEFAULT_HANDLER`` are defined in the
sibling module :mod:`ccsds_ndm.kvn_handlers` and re-exported here so that
``from ccsds_ndm.kvn_registry import TypeHandler`` works whether the
caller addresses the package or the module.

Schema-specific submodules (``ndmxml*.py``) are auto-discovered at import
time.  Each must expose a ``REGISTRY_INSTANCE`` with a ``version: int``
attribute.  The assembled mapping is available as ``VERSION_REGISTRY``.
"""

from __future__ import annotations

import importlib
import pkgutil

from ccsds_ndm.kvn_handlers import (  # noqa: F401
    DEFAULT_HANDLER,
    DISPATCH_CDM,
    DISPATCH_FLAT,
    DISPATCH_SEGMENTED,
    LOC_COVARIANCE,
    LOC_DEFAULT,
    LOC_PACKED_ATTITUDE,
    LOC_PACKED_LINES,
    LOC_PACKED_STATE,
    LOC_TDM_OBS,
    PARSE_COVARIANCE,
    PARSE_DEFAULT,
    PARSE_PACKED_ATTITUDE,
    PARSE_PACKED_LINES,
    PARSE_PACKED_STATE,
    PARSE_ROTATION_ANGLE,
    PARSE_ROTATION_RATE,
    PARSE_TDM_OBS,
    WRITE_COVARIANCE,
    WRITE_DEFAULT,
    WRITE_PACKED_ATTITUDE,
    WRITE_PACKED_LINES,
    WRITE_PACKED_STATE,
    WRITE_ROTATION_ANGLE,
    WRITE_ROTATION_RATE,
    WRITE_TDM_OBS,
    SchemaRegistry,
    TypeHandler,
)


def _discover_registries() -> dict[int, SchemaRegistry]:
    """
    Scan this package for ``ndmxml*.py`` submodules, import each one, and
    collect their ``REGISTRY_INSTANCE`` objects into a version-keyed dict.
    """
    result: dict[int, SchemaRegistry] = {}

    for _, module_name, _ in pkgutil.iter_modules(__path__):
        if not module_name.startswith("ndmxml"):  # skip non-schema submodules
            continue
        mod = importlib.import_module(f"{__name__}.{module_name}")  # dynamic import
        instance = getattr(mod, "REGISTRY_INSTANCE", None)
        if instance is None:
            raise ImportError(
                f"Registry submodule {module_name!r} has no REGISTRY_INSTANCE"
            )
        version = getattr(instance, "version", None)  # e.g. 2 for NDM XML 2.x
        if version is None:
            raise ImportError(
                f"REGISTRY_INSTANCE in {module_name!r} has no 'version' attribute"
            )
        if version in result:  # two submodules cannot claim the same NDM version
            raise ImportError(
                f"Duplicate registry version {version}: "
                f"{module_name!r} conflicts with an earlier module"
            )
        result[version] = instance
    return result


VERSION_REGISTRY: dict[int, SchemaRegistry] = _discover_registries()
