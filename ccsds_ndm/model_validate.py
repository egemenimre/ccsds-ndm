# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) CCSDS-NDM Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
Validation for xsdata model classes.

Patches ``__setattr__`` on container dataclasses so that assigning a value
of the wrong type to a field that expects a wrapper type (e.g. ``LengthType``,
``DvType``) raises ``TypeError`` with a clear message.

Patching runs automatically when this module is imported.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import pkgutil
import types
from enum import Enum
from typing import Union, get_args, get_origin, get_type_hints

# ---------------------------------------------------------------------------
# Type detection helpers
# ---------------------------------------------------------------------------


def _unwrap_optional(tp):
    """Given ``None | X`` or ``Optional[X]``, return X.  Otherwise return tp."""
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        # Drop NoneType; keep the single concrete type argument
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return tp


def _is_wrapper_type(cls, /) -> bool:
    """Return True if *cls* is a value+units wrapper dataclass."""
    if not dataclasses.is_dataclass(cls):
        return False
    fields = {f.name for f in dataclasses.fields(cls)}
    if "value" not in fields or "units" not in fields:
        return False
    try:
        hints = get_type_hints(cls)
    except Exception:
        return False
    units_type = _unwrap_optional(hints.get("units"))
    if units_type is None:
        return False
    # The units field must be backed by an Enum (the CCSDS unit strings enum)
    return isinstance(units_type, type) and issubclass(units_type, Enum)


# ---------------------------------------------------------------------------
# Field map construction
# ---------------------------------------------------------------------------


def _build_field_map(cls, wrapper_types: set[type]) -> dict[str, type]:
    """Build ``{field_name: wrapper_cls}`` for wrapper-typed fields on *cls*."""
    try:
        hints = get_type_hints(cls)
    except Exception:
        return {}

    field_map: dict[str, type] = {}
    for f in dataclasses.fields(cls):
        raw_type = hints.get(f.name)
        if raw_type is None:
            continue
        resolved = _unwrap_optional(raw_type)
        if not isinstance(resolved, type):
            continue
        # Only include fields whose type is a known wrapper (value+units dataclass)
        if resolved in wrapper_types:
            field_map[f.name] = resolved
    return field_map


# ---------------------------------------------------------------------------
# __setattr__ factory
# ---------------------------------------------------------------------------


def _make_setattr(field_map: dict[str, type]):
    """Return a ``__setattr__`` that validates wrapper-typed field assignments."""

    def __setattr__(self, name: str, value):
        wrapper_cls = field_map.get(name)
        if wrapper_cls is not None and value is not None:
            # Reject plain scalars, strings, or wrong wrapper types outright
            if not isinstance(value, wrapper_cls):
                raise TypeError(
                    f"Field '{name}' on {type(self).__name__} expects "
                    f"{wrapper_cls.__name__}, got "
                    f"{type(value).__name__}({value!r}). "
                    f"Use e.g. {wrapper_cls.__name__}(value=..., units=...)"
                )
        object.__setattr__(self, name, value)

    return __setattr__


# ---------------------------------------------------------------------------
# Module discovery and patching
# ---------------------------------------------------------------------------


def _get_submodules(package) -> list[types.ModuleType]:
    """Import and return all submodules of *package*."""
    modules = []
    for _, modname, _ in pkgutil.walk_packages(
        package.__path__, prefix=package.__name__ + "."
    ):
        try:
            modules.append(importlib.import_module(modname))
        except Exception:
            pass
    return modules


def _find_wrapper_types(modules: list[types.ModuleType]) -> set[type]:
    """Collect all wrapper types across *modules*."""
    wrappers: set[type] = set()
    for mod in modules:
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if _is_wrapper_type(cls):
                wrappers.add(cls)
    return wrappers


def _patch_module(module, wrapper_types: set[type]) -> None:
    """Patch all container dataclasses in *module*."""
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if not dataclasses.is_dataclass(cls):
            continue
        # Wrapper types themselves don't need a validating __setattr__
        if cls in wrapper_types:
            continue
        # Guard against patching the same class twice (e.g. re-imported modules)
        if getattr(cls, "_ndm_validated", False):
            continue
        field_map = _build_field_map(cls, wrapper_types)
        if not field_map:
            continue
        setattr(cls, "__setattr__", _make_setattr(field_map))
        setattr(cls, "_ndm_validated", True)


# ---------------------------------------------------------------------------
# Auto-patch on import
# ---------------------------------------------------------------------------


def _patch_all_models(patch_fn) -> None:
    """Iterate all model packages and call patch_fn(submodules, wrapper_types)."""
    import ccsds_ndm.models as models_pkg

    for _, pkg_name, is_pkg in pkgutil.iter_modules(
        models_pkg.__path__, models_pkg.__name__ + "."
    ):
        if not is_pkg:
            continue
        pkg = importlib.import_module(pkg_name)
        submodules = _get_submodules(pkg)
        # Collect all wrapper types for this schema version before patching,
        # so _build_field_map can resolve cross-module references correctly
        wrapper_types = _find_wrapper_types(submodules)
        patch_fn(submodules, wrapper_types)


def _apply_validation() -> None:
    """Patch all xsdata model classes for validation."""

    def patch(submodules, wrapper_types):
        for mod in submodules:
            _patch_module(mod, wrapper_types)

    _patch_all_models(patch)


_apply_validation()
