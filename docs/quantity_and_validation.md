# Type Validation and Quantity Support

## Overview

`ccsds-ndm` enforces type safety on the NDM object tree and offers seamless integration
with the [pint](https://pint.readthedocs.io/) and [astropy.units](https://docs.astropy.org/en/stable/units/)
quantity libraries.  Both features activate automatically the moment any part of
`ccsds_ndm.models` is imported — no extra setup is required.

Two opt-in modules are available:

- {mod}`ccsds_ndm.model_validate` — type validation only (no quantity library required).
- {mod}`ccsds_ndm.model_quantity` — type validation **plus** pint/astropy Quantity
  support.  This module supersedes `model_validate`; importing it alone is sufficient.

Because `ccsds_ndm.models.__init__` imports `model_quantity`, both features are active
in normal usage without an explicit import.

## Type Validation

Every field in the NDM object tree that holds a physical quantity is typed with a
*wrapper type* — a small dataclass that bundles a numeric `value` with a unit `units`
enum member (e.g. `LengthType`, `DvType`, `AngleType`).  Assigning a plain number,
`Decimal`, or string to such a field now raises a `TypeError` immediately.

```python
from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_common_2_0 import LengthType, LengthUnits
from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_cdm_1_0 import RelativeStateVectorType, DvType, DvUnits

sv = RelativeStateVectorType(
    relative_position_r=LengthType(value=700, units=LengthUnits.M),
    relative_position_t=LengthType(value=800, units=LengthUnits.M),
    relative_position_n=LengthType(value=900, units=LengthUnits.M),
    relative_velocity_r=DvType(value=10, units=DvUnits.M_S),
    relative_velocity_t=DvType(value=20, units=DvUnits.M_S),
    relative_velocity_n=DvType(value=30, units=DvUnits.M_S),
)

# Valid: reassign with the correct wrapper type
sv.relative_position_r = LengthType(value=750, units=LengthUnits.M)

# Valid: None is allowed on optional fields
sv.relative_position_r = None

# Invalid: plain numbers, Decimal, and strings all raise TypeError
sv.relative_position_r = 700          # TypeError
sv.relative_position_r = 700.0        # TypeError
sv.relative_position_r = Decimal(700) # TypeError
sv.relative_position_r = "700 m"      # TypeError
```

The error message names the field, the container class, the expected wrapper type, and
the value that was rejected, making it straightforward to diagnose the problem:

```text
TypeError: Field 'relative_position_r' on RelativeStateVectorType expects LengthType,
got int(700). Use e.g. LengthType(value=..., units=...)
or a pint/astropy Quantity.
```

Validation applies at both assignment time and at constructor time (dataclass
`__init__` calls `__setattr__` internally).

## Assigning pint Quantities

When `model_quantity` is active, a pint `Quantity` can be assigned directly to any
wrapper-typed field.  The library matches the incoming unit against the accepted CCSDS
unit strings for that field and wraps the value automatically — **no unit conversion is
performed**.

```python
import pint
u = pint.UnitRegistry()

sv.relative_position_r = 700 * u.m      # → LengthType(value=700.0, units=LengthUnits.M)
sv.relative_velocity_r  = 10 * u.m / u.s  # → DvType(value=10.0, units=DvUnits.M_S)
```

If the unit is dimensionally correct but not one of the accepted CCSDS strings, a
`TypeError` is raised listing the accepted options so you can convert beforehand:

```python
sv.relative_position_r = 0.7 * u.km
# TypeError: Unit 'kilometer' is not accepted for field 'relative_position_r' …
# Accepted units for LengthType: ['m']. Convert your Quantity first.
```

If the unit has the wrong physical dimension entirely, the error message says so:

```python
sv.relative_position_r = 10 * u.m / u.s
# TypeError: Cannot assign [length] / [time] quantity … Dimensions are incompatible.
```

pint Quantities can also be passed directly to the dataclass constructor:

```python
sv = RelativeStateVectorType(
    relative_position_r=700 * u.m,
    relative_position_t=800 * u.m,
    relative_position_n=900 * u.m,
    relative_velocity_r=10 * u.m / u.s,
    relative_velocity_t=20 * u.m / u.s,
    relative_velocity_n=30 * u.m / u.s,
)
```

---

## Assigning astropy Quantities

The same behaviour applies for `astropy.units.Quantity`:

```python
from astropy import units as astropy_u

sv.relative_position_r = 700 * astropy_u.m   # → LengthType(value=700.0, units=LengthUnits.M)
sv.relative_velocity_r  = 10 * astropy_u.m / astropy_u.s
```

Unit mismatch errors follow the same pattern as for pint.

---

## Extracting Quantities with `.q()`

Every wrapper instance gains a `.q()` method that returns a `Quantity` in the
currently configured backend (pint or astropy):

```python
from ccsds_ndm.model_quantity import set_quantity_mode, QuantityMode

lt = LengthType(value=700, units=LengthUnits.M)

set_quantity_mode(QuantityMode.PINT)
q = lt.q()        # pint Quantity: 700 meter
print(q.magnitude, q.units)  # 700.0  meter

set_quantity_mode(QuantityMode.ASTROPY)
q = lt.q()        # astropy Quantity: 700. m
print(q.value, q.unit)       # 700.0  m
```

`.q()` also works directly on fields of a container object:

```python
q = sv.relative_position_r.q()   # pint or astropy Quantity, depending on mode
```

### Quantity mode

| Mode | Import | `.q()` returns |
|------|--------|----------------|
| `QuantityMode.ASTROPY` | `astropy` (default) | `astropy.units.Quantity` |
| `QuantityMode.PINT` | `pint` | `pint.Quantity` |

Switch modes at any time with {func}`ccsds_ndm.model_quantity.set_quantity_mode`.
The mode is global and affects all subsequent `.q()` calls.

---

## CCSDS Unit Strings and Library Mappings

Some CCSDS unit strings are non-standard and require translation before being passed
to pint or astropy.  The mapping is applied internally:

| CCSDS string | pint equivalent           | astropy equivalent |
|--------------|---------------------------|--------------------|
| `rev/day`    | `revolution/day`          | `cycle/d`          |
| `rev/day**2` | `revolution/day**2`       | `cycle/d**2`       |
| `rev/day**3` | `revolution/day**3`       | `cycle/d**3`       |
| `1/ER`       | `1/earth_radius` (custom) | `1/earthRad`       |
| `#/yr`       | `1/year`                  | `1/yr`             |

The pint registry defines `earth_radius = 6378.135 km` (SGP4/TLE convention, matching
Hoots & Roehrich 1980) with aliases `ER` and `R_earth`.

`SFU` (solar flux unit) has no equivalent in either library.  Calling `.q()` on a
field with `SFU` units returns a dimensionless `Quantity` and emits a `UserWarning`.

---

## Using Only Validation (No Quantity Library)

If you do not need pint or astropy integration, you can import only the validation
module.  The behaviour is identical to `model_quantity` except that pint/astropy
Quantities are not accepted as input and `.q()` is not patched onto wrapper types.

```python
import ccsds_ndm.model_validate  # activates type checking only
```

In practice this import is rarely needed explicitly, since importing any module from
`ccsds_ndm.models` already activates the full `model_quantity` support.

---

## Optional Dependencies

pint and astropy are optional.  Install whichever backend you need:

```bash
pip install ccsds_ndm[pint]
pip install ccsds_ndm[astropy]
pip install ccsds_ndm[pint,astropy]   # both
```
