# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) CCSDS-NDM Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
Validation and quantity support for xsdata model classes.

Patches ``__setattr__`` on container dataclasses so that:

- Already-wrapped values (e.g. ``LengthType``) pass through unchanged.
- pint / astropy Quantity objects are converted to the correct wrapper type
  with unit conversion and dimensional validation.
- Plain numbers, strings, and other invalid types raise ``TypeError``.
- ``None`` is allowed on optional fields.

Also patches a ``.q()`` method on wrapper types (dataclasses with ``value``
and ``units`` fields) that returns a pint or astropy Quantity, controlled by
a global mode flag.

Patching runs automatically when this module is imported.
"""

from __future__ import annotations

import dataclasses
import inspect
import warnings
from enum import Enum
from typing import get_type_hints

from ccsds_ndm.model_validate import (
    _patch_all_models,
    _unwrap_optional,
)

# ---------------------------------------------------------------------------
# Global quantity mode
# ---------------------------------------------------------------------------


class QuantityMode(Enum):
    """Quantity backend selection."""

    PINT = "pint"
    ASTROPY = "astropy"


# Default to astropy; can be switched at runtime via set_quantity_mode()
_quantity_mode: QuantityMode = QuantityMode.ASTROPY


def set_quantity_mode(mode: object) -> None:
    """Set the global quantity mode for ``.q()`` on wrapper types."""
    global _quantity_mode
    if not isinstance(mode, QuantityMode):
        raise TypeError(
            f"Expected QuantityMode, got {type(mode).__name__}. "
            f"Use QuantityMode.PINT or QuantityMode.ASTROPY."
        )
    _quantity_mode = mode


def get_quantity_mode() -> QuantityMode:
    """Return the current global quantity mode."""
    return _quantity_mode


# ---------------------------------------------------------------------------
# Global auto-convert flag
# ---------------------------------------------------------------------------

# When True, dimensionally compatible Quantities are automatically converted
# to the field's default CCSDS unit instead of raising TypeError.
_auto_convert: bool = False


def set_auto_convert(enabled: object) -> None:
    """Enable or disable automatic unit conversion on Quantity assignment."""
    global _auto_convert
    if not isinstance(enabled, bool):
        raise TypeError(f"Expected bool, got {type(enabled).__name__}.")
    _auto_convert = enabled


def get_auto_convert() -> bool:
    """Return whether automatic unit conversion is enabled."""
    return _auto_convert


# ---------------------------------------------------------------------------
# CCSDS <-> pint / astropy unit string mappings
# ---------------------------------------------------------------------------

# pint does not recognise "rev/day" or "#/yr" natively; map them to
# pint's canonical spelling.  Keys cover both lower- and upper-case
# variants that appear in NDM XML/KVN files.
_CCSDS_TO_PINT: dict[str, str] = {
    "rev/day": "revolution/day",
    "rev/day**2": "revolution/day**2",
    "rev/day**3": "revolution/day**3",
    "REV/DAY": "revolution/day",
    "REV/DAY**2": "revolution/day**2",
    "REV/DAY**3": "revolution/day**3",
    "#/yr": "1/year",
}

# astropy uses "cycle" for revolutions and "d" for day.
# "1/ER" (inverse Earth-radius, BSTAR unit) maps to astropy's built-in
# earthRad constant.  "SFU" (solar flux unit) has no astropy equivalent
# and is listed in _UNSUPPORTED_UNITS instead.
_CCSDS_TO_ASTROPY: dict[str, str] = {
    "rev/day": "cycle/d",
    "rev/day**2": "cycle/d**2",
    "rev/day**3": "cycle/d**3",
    "REV/DAY": "cycle/d",
    "REV/DAY**2": "cycle/d**2",
    "REV/DAY**3": "cycle/d**3",
    "1/ER": "1/earthRad",
    "#/yr": "1/yr",
}

# CCSDS unit strings that have no equivalent in either pint or astropy.
# Fields with these units return a dimensionless Quantity with a warning.
_UNSUPPORTED_UNITS: set[str] = {"SFU"}


def _ccsds_to_pint(unit_str: str) -> str:
    """Convert a CCSDS unit string to its pint equivalent."""
    return _CCSDS_TO_PINT.get(unit_str, unit_str)


def _ccsds_to_astropy(unit_str: str) -> str:
    """Convert a CCSDS unit string to its astropy equivalent."""
    return _CCSDS_TO_ASTROPY.get(unit_str, unit_str)


# ---------------------------------------------------------------------------
# Cached pint UnitRegistry
# ---------------------------------------------------------------------------

_pint_ureg = (
    None  # lazily initialised on first use to avoid importing pint at load time
)


def _get_pint_ureg():
    """Return a cached pint ``UnitRegistry`` with custom CCSDS units."""
    global _pint_ureg
    if _pint_ureg is None:
        import pint

        _pint_ureg = pint.UnitRegistry()

        # ER = Earth Radius as used in SGP4 (Hoots & Roehrich 1980).
        # Intentionally differs from WGS84 (6378.137 km) to keep BSTAR values
        # consistent with the TLE convention that defines the unit.
        _pint_ureg.define("earth_radius = 6378.135 km = ER = R_earth")
    return _pint_ureg


# ---------------------------------------------------------------------------
# Type detection helpers
# ---------------------------------------------------------------------------


def _is_pint_quantity(value) -> bool:
    """Check if *value* is a pint Quantity without importing pint."""
    t = type(value)
    return t.__module__.startswith("pint") and t.__name__ == "Quantity"


def _is_astropy_quantity(value) -> bool:
    """Check if *value* is an astropy Quantity without importing astropy."""
    t = type(value)
    return t.__module__.startswith("astropy") and t.__name__ == "Quantity"


def _get_units_enum(wrapper_cls) -> type[Enum]:
    """Extract the units Enum class from a wrapper type's type hints."""
    hints = get_type_hints(wrapper_cls)
    return _unwrap_optional(hints["units"])


# ---------------------------------------------------------------------------
# Unit matching helpers
# ---------------------------------------------------------------------------


def _accepted_unit_strings(units_enum: type[Enum]) -> list[str]:
    """Return CCSDS unit strings for all supported (non-_UNSUPPORTED) members."""
    return [m.value for m in units_enum if m.value not in _UNSUPPORTED_UNITS]


def _match_pint_unit(value, units_enum: type[Enum]) -> tuple[object, bool]:
    """Return ``(matched_member_or_None, dimensions_ok)`` for a pint Quantity.

    Re-parses the incoming unit string through our registry to handle
    cross-registry comparisons safely.
    """
    import pint

    u = _get_pint_ureg()
    try:
        # Re-parse the incoming unit through our registry; this normalises
        # quantities that may come from a different pint UnitRegistry instance,
        # making dimensionality and unit comparisons safe across registries.
        incoming = u.Quantity(f"1 {value.units}")
    except pint.errors.PintError:
        # Unrecognised unit string — cannot match anything
        return None, False

    matched = None
    dims_ok = False
    for member in units_enum:
        ccsds_str = member.value
        if ccsds_str in _UNSUPPORTED_UNITS:
            # Skip units that have no pint equivalent (e.g. non-SI CCSDS units)
            continue
        try:
            target = u.Quantity(f"1 {_ccsds_to_pint(ccsds_str)}")
        except pint.errors.PintError:
            # Mapping produced a unit string pint still can't parse — skip
            continue
        if incoming.dimensionality == target.dimensionality:
            dims_ok = True  # at least one member shares the same dimensions
            if incoming.units == target.units:
                return member, True  # exact unit match found
    return matched, dims_ok


def _match_astropy_unit(value, units_enum: type[Enum]) -> tuple[object, bool]:
    """Return ``(matched_member_or_None, dimensions_ok)`` for an astropy Quantity."""
    from astropy import units as astropy_u

    matched = None
    dims_ok = False
    for member in units_enum:
        ccsds_str = member.value
        if ccsds_str in _UNSUPPORTED_UNITS:
            # Skip units that have no astropy equivalent (e.g. non-SI CCSDS units)
            continue
        try:
            target = astropy_u.Unit(_ccsds_to_astropy(ccsds_str))
        except (astropy_u.core.UnitsError, ValueError):
            # Mapping produced a unit string astropy still can't parse — skip
            continue
        if value.unit.physical_type == target.physical_type:
            dims_ok = True  # at least one member shares the same physical type
            if value.unit == target:
                return member, True  # exact unit match found
    return matched, dims_ok


# ---------------------------------------------------------------------------
# Auto-convert helpers
# ---------------------------------------------------------------------------


def _default_unit_member(units_enum: type[Enum]) -> Enum | None:
    """Return the first supported enum member (the NDM default unit)."""
    for member in units_enum:
        if member.value not in _UNSUPPORTED_UNITS:
            return member
    return None


def _convert_pint(value, target_member) -> float:
    """Convert a pint Quantity to *target_member*'s unit; return magnitude."""
    u = _get_pint_ureg()
    target_unit = u.Unit(_ccsds_to_pint(target_member.value))
    converted = u.Quantity(f"{value.magnitude} {value.units}").to(target_unit)
    return float(converted.magnitude)


def _convert_astropy(value, target_member) -> float:
    """Convert an astropy Quantity to *target_member*'s unit; return value."""
    from astropy import units as astropy_u

    target_unit = astropy_u.Unit(_ccsds_to_astropy(target_member.value))
    converted = value.to(target_unit)
    return float(converted.value)


# ---------------------------------------------------------------------------
# Field map construction
# ---------------------------------------------------------------------------

_FieldInfo = tuple  # (wrapper_cls, units_enum_cls)


def _build_field_map(cls, wrapper_types: set[type]) -> dict[str, _FieldInfo]:
    """Build ``{field_name: (wrapper_cls, units_enum_cls)}`` for *cls*."""
    try:
        hints = get_type_hints(cls)
    except Exception:
        return {}

    field_map: dict[str, _FieldInfo] = {}
    for f in dataclasses.fields(cls):
        raw_type = hints.get(f.name)
        if raw_type is None:
            continue
        resolved = _unwrap_optional(raw_type)
        if not isinstance(resolved, type):
            continue
        # Only include fields whose type is a known wrapper (value+units dataclass)
        if resolved not in wrapper_types:
            continue
        units_enum = _get_units_enum(resolved)
        field_map[f.name] = (resolved, units_enum)
    return field_map


# ---------------------------------------------------------------------------
# __setattr__ factory for container types
# ---------------------------------------------------------------------------


def _resolve_quantity(
    value,
    name: str,
    owner_type: str,
    wrapper_cls,
    units_enum,
    matched,
    dims_ok: bool,
    unit_attr: str,
    mag_attr: str,
    convert_fn,
):
    """Convert a pint/astropy Quantity to the correct wrapper, or raise TypeError.

    Parameters
    ----------
    unit_attr:
        Attribute name for the unit on *value* (``"units"`` for pint,
        ``"unit"`` for astropy).
    mag_attr:
        Attribute name for the magnitude on *value* (``"magnitude"`` for
        pint, ``"value"`` for astropy).
    convert_fn:
        Library-specific conversion helper (``_convert_pint`` or
        ``_convert_astropy``).
    """
    if matched is not None:
        return wrapper_cls(value=float(getattr(value, mag_attr)), units=matched)
    unit_str = getattr(value, unit_attr)
    accepted = _accepted_unit_strings(units_enum)
    if dims_ok:
        default = _default_unit_member(units_enum)
        if default is not None and _auto_convert:
            try:
                return wrapper_cls(value=convert_fn(value, default), units=default)
            except Exception:
                raise TypeError(
                    f"Unit '{unit_str}' could not be auto-converted "
                    f"for field '{name}' on {owner_type}. "
                    f"Accepted units for {wrapper_cls.__name__}: {accepted}."
                )
        raise TypeError(
            f"Unit '{unit_str}' is not accepted for field '{name}' on {owner_type}. "
            f"Accepted units for {wrapper_cls.__name__}: {accepted}. "
            f"Convert your Quantity first."
        )
    raise TypeError(
        f"Cannot assign {unit_str} quantity to field '{name}' on {owner_type} "
        f"which expects {wrapper_cls.__name__}. Dimensions are incompatible."
    )


def _make_setattr(field_map: dict[str, _FieldInfo]):
    """Return a ``__setattr__`` that validates and wraps Quantities.

    By default the unit of the incoming Quantity must exactly match one of the
    accepted CCSDS unit strings for the field.  When ``_auto_convert`` is
    enabled, dimensionally compatible Quantities are silently converted to
    the field's default CCSDS unit instead of raising ``TypeError``.
    """

    def __setattr__(self, name: str, value):
        info = field_map.get(name)
        if info is not None and value is not None:
            wrapper_cls, units_enum = info
            if isinstance(value, wrapper_cls):
                pass  # already the correct wrapper type
            elif _is_pint_quantity(value):
                matched, dims_ok = _match_pint_unit(value, units_enum)
                value = _resolve_quantity(
                    value,
                    name,
                    type(self).__name__,
                    wrapper_cls,
                    units_enum,
                    matched,
                    dims_ok,
                    "units",
                    "magnitude",
                    _convert_pint,
                )
            elif _is_astropy_quantity(value):
                matched, dims_ok = _match_astropy_unit(value, units_enum)
                value = _resolve_quantity(
                    value,
                    name,
                    type(self).__name__,
                    wrapper_cls,
                    units_enum,
                    matched,
                    dims_ok,
                    "unit",
                    "value",
                    _convert_astropy,
                )
            else:
                # Not a wrapper, not a Quantity — reject with a helpful message
                raise TypeError(
                    f"Field '{name}' on {type(self).__name__} expects "
                    f"{wrapper_cls.__name__}, got "
                    f"{type(value).__name__}({value!r}). "
                    f"Use e.g. {wrapper_cls.__name__}(value=..., units=...) "
                    f"or a pint/astropy Quantity."
                )
        object.__setattr__(self, name, value)

    return __setattr__


# ---------------------------------------------------------------------------
# .q() method for wrapper types
# ---------------------------------------------------------------------------


def _make_wrapper_q():
    """Return a ``.q()`` method to be patched onto wrapper types."""

    def q(self):
        """Return this value as a pint or astropy Quantity."""
        mode = get_quantity_mode()
        # Extract the raw CCSDS unit string (e.g. "km", "1/ER") from the enum
        unit_str = (
            self.units.value
            if hasattr(self, "units") and self.units is not None
            else None
        )

        unsupported = unit_str in _UNSUPPORTED_UNITS
        if unsupported:
            warnings.warn(
                f"CCSDS unit '{unit_str}' has no equivalent; "
                f"returning dimensionless Quantity.",
                stacklevel=2,
            )

        # Collapse the two None/unsupported guards into one variable
        effective_unit = None if (unit_str is None or unsupported) else unit_str

        if mode is QuantityMode.PINT:
            u = _get_pint_ureg()
            if effective_unit is None:
                return u.Quantity(self.value)
            return u.Quantity(f"{self.value} {_ccsds_to_pint(effective_unit)}")

        else:  # QuantityMode.ASTROPY
            from astropy import units as astropy_u

            if effective_unit is None:
                return astropy_u.Quantity(self.value)
            return astropy_u.Quantity(
                f"{self.value} {_ccsds_to_astropy(effective_unit)}"
            )

    return q


# ---------------------------------------------------------------------------
# Module discovery and patching
# ---------------------------------------------------------------------------


def _patch_module(module, wrapper_types: set[type], wrapper_q) -> None:
    """Patch all dataclasses in *module*."""
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if not dataclasses.is_dataclass(cls):
            continue
        # Guard against patching the same class twice (e.g. re-imported modules)
        if getattr(cls, "_ndm_quantity_patched", False):
            continue

        if cls in wrapper_types:
            # Wrapper types get a .q() method so users can extract a Quantity
            setattr(cls, "q", wrapper_q)
            setattr(cls, "_ndm_quantity_patched", True)
        else:
            field_map = _build_field_map(cls, wrapper_types)
            if not field_map:
                continue
            # Container types get a validating __setattr__ for their wrapper fields
            setattr(cls, "__setattr__", _make_setattr(field_map))
            setattr(cls, "_ndm_quantity_patched", True)


def _apply_quantity_support() -> None:
    """Patch all xsdata model classes. Called at import time."""
    wrapper_q = _make_wrapper_q()

    def patch(submodules, wrapper_types):
        for mod in submodules:
            _patch_module(mod, wrapper_types, wrapper_q)

    _patch_all_models(patch)


_apply_quantity_support()
