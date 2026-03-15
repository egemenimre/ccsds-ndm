# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
Tests for the merged validation + quantity support on xsdata model classes.
"""

from decimal import Decimal
from pathlib import Path

import pytest

# Importing model_quantity triggers patching
import ccsds_ndm.model_quantity  # noqa: F401
from ccsds_ndm.model_quantity import (
    QuantityMode,
    get_auto_convert,
    get_quantity_mode,
    set_auto_convert,
    set_quantity_mode,
)

# ndmxml2 imports
from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_cdm_1_0 import (
    DvType,
    DvUnits,
    RelativeMetadataData,
    RelativeStateVectorType,
)
from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_common_2_0 import LengthType, LengthUnits

# ndmxml4 imports
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_cdm_1_0 import DvType as DvType4
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_cdm_1_0 import DvUnits as DvUnits4
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_cdm_1_0 import (
    RelativeStateVectorType as RelativeStateVectorType4,
)
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_common_4_0 import LengthTypeUo
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_common_4_0 import LengthUnits as LengthUnits4


def _make_sv():
    """Create a valid RelativeStateVectorType (ndmxml2)."""
    return RelativeStateVectorType(
        relative_position_r=LengthType(value=700, units=LengthUnits.M),
        relative_position_t=LengthType(value=800, units=LengthUnits.M),
        relative_position_n=LengthType(value=900, units=LengthUnits.M),
        relative_velocity_r=DvType(value=10, units=DvUnits.M_S),
        relative_velocity_t=DvType(value=20, units=DvUnits.M_S),
        relative_velocity_n=DvType(value=30, units=DvUnits.M_S),
    )


def _make_sv4():
    """Create a valid RelativeStateVectorType (ndmxml4)."""
    return RelativeStateVectorType4(
        relative_position_r=LengthTypeUo(value=700, units=LengthUnits4.M),
        relative_position_t=LengthTypeUo(value=800, units=LengthUnits4.M),
        relative_position_n=LengthTypeUo(value=900, units=LengthUnits4.M),
        relative_velocity_r=DvType4(value=10, units=DvUnits4.M_S),
        relative_velocity_t=DvType4(value=20, units=DvUnits4.M_S),
        relative_velocity_n=DvType4(value=30, units=DvUnits4.M_S),
    )


# ---- Rejection of plain numbers ----


class TestRejectPlainNumbers:
    """Assigning plain numbers to wrapper-typed fields must raise TypeError."""

    def test_plain_int_raises(self):
        sv = _make_sv()
        with pytest.raises(TypeError, match="expects LengthType"):
            sv.relative_position_r = 700  # type: ignore[assignment]

    def test_plain_float_raises(self):
        sv = _make_sv()
        with pytest.raises(TypeError, match="expects LengthType"):
            sv.relative_position_r = 700.0  # type: ignore[assignment]

    def test_decimal_raises(self):
        sv = _make_sv()
        with pytest.raises(TypeError, match="expects LengthType"):
            sv.relative_position_r = Decimal("700")  # type: ignore[assignment]

    def test_string_raises(self):
        sv = _make_sv()
        with pytest.raises(TypeError, match="expects LengthType"):
            sv.relative_position_r = "bad"  # type: ignore[assignment]

    def test_construction_with_plain_int_raises(self):
        with pytest.raises(TypeError, match="expects LengthType"):
            RelativeStateVectorType(
                relative_position_r=700,  # type: ignore[arg-type]
                relative_position_t=LengthType(value=800, units=LengthUnits.M),
                relative_position_n=LengthType(value=900, units=LengthUnits.M),
                relative_velocity_r=DvType(value=10, units=DvUnits.M_S),
                relative_velocity_t=DvType(value=20, units=DvUnits.M_S),
                relative_velocity_n=DvType(value=30, units=DvUnits.M_S),
            )


# ---- Correct wrapper type passes ----


class TestCorrectWrapperPasses:
    """Correct wrapper types and None must pass through."""

    def test_correct_wrapper_passes(self):
        sv = _make_sv()
        new_val = LengthType(value=999, units=LengthUnits.M)
        sv.relative_position_r = new_val
        assert sv.relative_position_r is new_val

    def test_none_passes_optional(self):
        rmd = RelativeMetadataData(
            tca="2010-03-13T22:37:52.618",
            miss_distance=LengthType(value=715, units=LengthUnits.M),
        )
        rmd.relative_speed = None
        assert rmd.relative_speed is None

    def test_set_then_clear_optional(self):
        rmd = RelativeMetadataData(
            tca="2010-03-13T22:37:52.618",
            miss_distance=LengthType(value=715, units=LengthUnits.M),
        )
        rmd.relative_speed = DvType(value=500, units=DvUnits.M_S)
        assert isinstance(rmd.relative_speed, DvType)
        rmd.relative_speed = None
        assert rmd.relative_speed is None

    def test_construction_with_wrappers_ok(self):
        sv = _make_sv()
        assert isinstance(sv.relative_position_r, LengthType)
        assert sv.relative_position_r.value == 700.0
        assert sv.relative_position_r.units == LengthUnits.M
        assert isinstance(sv.relative_velocity_r, DvType)
        assert sv.relative_velocity_r.value == 10.0


# ---- Error message format ----


class TestErrorMessageFormat:
    """Error messages must include field name, class name, and expected type."""

    def test_message_includes_field_and_class(self):
        sv = _make_sv()
        with pytest.raises(TypeError) as exc_info:
            sv.relative_position_r = 600  # type: ignore[assignment]
        msg = str(exc_info.value)
        assert "relative_position_r" in msg
        assert "RelativeStateVectorType" in msg
        assert "LengthType" in msg
        assert "int" in msg
        assert "600" in msg


# ---- pint setter ----


class TestPintSetter:
    """Assigning pint Quantities wraps without conversion; unit must be accepted."""

    def test_accepted_unit(self):
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = _make_sv()
        sv.relative_position_r = 700 * u.m
        assert isinstance(sv.relative_position_r, LengthType)
        assert sv.relative_position_r.value == pytest.approx(700.0)
        assert sv.relative_position_r.units == LengthUnits.M

    def test_unaccepted_unit_same_dimension_raises(self):
        """km is a valid length but not in LengthUnits — must raise."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = _make_sv()
        with pytest.raises(TypeError, match="not accepted"):
            sv.relative_position_r = 0.7 * u.km

    def test_construction_time(self):
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = RelativeStateVectorType(
            relative_position_r=700 * u.m,
            relative_position_t=800 * u.m,
            relative_position_n=900 * u.m,
            relative_velocity_r=10 * u.m / u.s,
            relative_velocity_t=20 * u.m / u.s,
            relative_velocity_n=30 * u.m / u.s,
        )
        assert isinstance(sv.relative_position_r, LengthType)
        assert sv.relative_position_r.value == pytest.approx(700.0)

    def test_velocity_quantity(self):
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = _make_sv()
        sv.relative_velocity_r = 10 * u.m / u.s
        assert isinstance(sv.relative_velocity_r, DvType)
        assert sv.relative_velocity_r.value == pytest.approx(10.0)

    def test_error_message_lists_accepted_units(self):
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = _make_sv()
        with pytest.raises(TypeError) as exc_info:
            sv.relative_position_r = 0.7 * u.km
        assert "m" in str(exc_info.value)  # accepted unit listed


# ---- astropy setter ----


class TestAstropySetter:
    """Assigning astropy Quantities wraps without conversion; unit must be accepted."""

    def test_accepted_unit(self):
        astropy_u = pytest.importorskip("astropy.units")
        sv = _make_sv()
        sv.relative_position_r = 700 * astropy_u.m
        assert isinstance(sv.relative_position_r, LengthType)
        assert sv.relative_position_r.value == pytest.approx(700.0)
        assert sv.relative_position_r.units == LengthUnits.M

    def test_unaccepted_unit_same_dimension_raises(self):
        """km is a valid length but not in LengthUnits — must raise."""
        astropy_u = pytest.importorskip("astropy.units")
        sv = _make_sv()
        with pytest.raises(TypeError, match="not accepted"):
            sv.relative_position_r = 0.7 * astropy_u.km

    def test_construction_time(self):
        astropy_u = pytest.importorskip("astropy.units")
        sv = RelativeStateVectorType(
            relative_position_r=700 * astropy_u.m,
            relative_position_t=800 * astropy_u.m,
            relative_position_n=900 * astropy_u.m,
            relative_velocity_r=10 * astropy_u.m / astropy_u.s,
            relative_velocity_t=20 * astropy_u.m / astropy_u.s,
            relative_velocity_n=30 * astropy_u.m / astropy_u.s,
        )
        assert isinstance(sv.relative_position_r, LengthType)
        assert sv.relative_position_r.value == pytest.approx(700.0)


# ---- Dimensional validation ----


class TestDimensionalValidation:
    """Assigning dimensionally incompatible Quantities must raise TypeError."""

    def test_pint_velocity_to_length_raises(self):
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = _make_sv()
        with pytest.raises(TypeError, match="incompatible"):
            sv.relative_position_r = 10 * u.m / u.s

    def test_pint_length_to_velocity_raises(self):
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = _make_sv()
        with pytest.raises(TypeError, match="incompatible"):
            sv.relative_velocity_r = 700 * u.m

    def test_astropy_velocity_to_length_raises(self):
        astropy_u = pytest.importorskip("astropy.units")
        sv = _make_sv()
        with pytest.raises(TypeError, match="incompatible"):
            sv.relative_position_r = 10 * astropy_u.m / astropy_u.s

    def test_astropy_length_to_velocity_raises(self):
        astropy_u = pytest.importorskip("astropy.units")
        sv = _make_sv()
        with pytest.raises(TypeError, match="incompatible"):
            sv.relative_velocity_r = 700 * astropy_u.m


# ---- .q() on wrapper types ----


class TestWrapperQ:
    """.q() on wrapper instances must return pint or astropy Quantities."""

    def test_pint_mode(self):
        pytest.importorskip("pint")
        set_quantity_mode(QuantityMode.PINT)
        lt = LengthType(value=700, units=LengthUnits.M)
        q = lt.q()  # type: ignore[attr-defined]
        assert q.magnitude == pytest.approx(700.0)
        assert str(q.units) == "meter"

    def test_astropy_mode(self):
        astropy_u = pytest.importorskip("astropy.units")
        set_quantity_mode(QuantityMode.ASTROPY)
        try:
            lt = LengthType(value=700, units=LengthUnits.M)
            q = lt.q()  # type: ignore[attr-defined]
            assert q.value == pytest.approx(700.0)
            assert q.unit == astropy_u.m
        finally:
            set_quantity_mode(QuantityMode.PINT)

    def test_q_on_velocity(self):
        pytest.importorskip("pint")
        set_quantity_mode(QuantityMode.PINT)
        dv = DvType(value=10, units=DvUnits.M_S)
        q = dv.q()  # type: ignore[attr-defined]
        assert q.magnitude == pytest.approx(10.0)
        assert "meter / second" in str(q.units)

    def test_q_via_container_field(self):
        """sv.relative_position_r.q() must work."""
        pytest.importorskip("pint")
        set_quantity_mode(QuantityMode.PINT)
        sv = _make_sv()
        q = sv.relative_position_r.q()  # type: ignore[attr-defined]
        assert q.magnitude == pytest.approx(700.0)

    def test_unsupported_units_warning(self):
        pytest.importorskip("pint")
        from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_common_4_0 import (
            SolarFluxType,
            SolarFluxUnits,
        )

        set_quantity_mode(QuantityMode.PINT)
        sf = SolarFluxType(value=100, units=SolarFluxUnits.SFU)
        with pytest.warns(UserWarning, match="no equivalent"):
            q = sf.q()  # type: ignore[attr-defined]
        assert q.magnitude == pytest.approx(100.0)


# ---- set_quantity_mode ----


class TestSetQuantityMode:
    """set_quantity_mode must accept QuantityMode enum values."""

    def test_set_pint(self):
        set_quantity_mode(QuantityMode.PINT)
        assert get_quantity_mode() is QuantityMode.PINT

    def test_set_astropy(self):
        set_quantity_mode(QuantityMode.ASTROPY)
        assert get_quantity_mode() is QuantityMode.ASTROPY
        set_quantity_mode(QuantityMode.PINT)  # reset

    def test_invalid_mode_raises(self):
        with pytest.raises(TypeError, match="Expected QuantityMode"):
            set_quantity_mode("pint")  # type: ignore[arg-type]


# ---- ndmxml4 tests ----


class TestNdmxml4:
    """Verify patching works with ndmxml4 Uo/Ur variant types."""

    def test_plain_int_raises(self):
        sv = _make_sv4()
        with pytest.raises(TypeError, match="expects LengthTypeUo"):
            sv.relative_position_r = 700  # type: ignore[assignment]

    def test_correct_wrapper_passes(self):
        sv = _make_sv4()
        new_val = LengthTypeUo(value=999, units=LengthUnits4.M)
        sv.relative_position_r = new_val
        assert sv.relative_position_r is new_val

    def test_q_on_ndmxml4_wrapper(self):
        pytest.importorskip("pint")
        set_quantity_mode(QuantityMode.PINT)
        lt = LengthTypeUo(value=700, units=LengthUnits4.M)
        q = lt.q()  # type: ignore[attr-defined]
        assert q.magnitude == pytest.approx(700.0)


# ---- Idempotency ----


class TestIdempotency:
    """Importing model_quantity twice must not break anything."""

    def test_double_import(self):
        import importlib

        importlib.reload(ccsds_ndm.model_quantity)
        sv = _make_sv()
        assert isinstance(sv.relative_position_r, LengthType)
        with pytest.raises(TypeError):
            sv.relative_position_r = 700  # type: ignore[assignment]


# ---- Round-trip I/O ----


class TestRoundTrip:
    """Quantity support must not break KVN/XML serialization."""

    def test_kvn_round_trip(self):
        from ccsds_ndm.ndm_io import NdmIo

        kvn_path = Path("tests", "data", "kvn", "cdm_example_section4.kvn")
        if not kvn_path.exists():
            pytest.skip("CDM KVN test file not found")

        ndm = NdmIo().from_path(kvn_path)
        sv = ndm.body.relative_metadata_data.relative_state_vector  # type: ignore[union-attr]
        assert hasattr(sv.relative_position_r, "value")
        assert hasattr(sv.relative_position_r, "units")

    def test_xml_round_trip(self):
        from ccsds_ndm.ndm_io import NdmIo

        xml_path = Path("tests", "data", "xml", "cdm_example_section4.xml")
        if not xml_path.exists():
            pytest.skip("CDM XML test file not found")

        ndm = NdmIo().from_path(xml_path)
        sv = ndm.body.relative_metadata_data.relative_state_vector  # type: ignore[union-attr]
        assert hasattr(sv.relative_position_r, "value")
        assert hasattr(sv.relative_position_r, "units")


# ---- Auto-convert ----


class TestAutoConvert:
    """Auto-convert flag silently converts Quantities to the NDM default unit."""

    def test_pint_auto_convert_length(self):
        """km → m conversion when auto_convert is on."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        set_auto_convert(True)
        try:
            sv = _make_sv()
            sv.relative_position_r = 0.7 * u.km
            assert isinstance(sv.relative_position_r, LengthType)
            assert sv.relative_position_r.value == pytest.approx(700.0)
            assert sv.relative_position_r.units == LengthUnits.M
        finally:
            set_auto_convert(False)

    def test_astropy_auto_convert_length(self):
        """km → m conversion with astropy when auto_convert is on."""
        astropy_u = pytest.importorskip("astropy.units")
        set_auto_convert(True)
        try:
            sv = _make_sv()
            sv.relative_position_r = 0.7 * astropy_u.km
            assert isinstance(sv.relative_position_r, LengthType)
            assert sv.relative_position_r.value == pytest.approx(700.0)
            assert sv.relative_position_r.units == LengthUnits.M
        finally:
            set_auto_convert(False)

    def test_pint_auto_convert_velocity(self):
        """km/s → m/s conversion when auto_convert is on."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        set_auto_convert(True)
        try:
            sv = _make_sv()
            sv.relative_velocity_r = 10 * u.km / u.s
            assert isinstance(sv.relative_velocity_r, DvType)
            assert sv.relative_velocity_r.value == pytest.approx(10000.0)
            assert sv.relative_velocity_r.units == DvUnits.M_S
        finally:
            set_auto_convert(False)

    def test_disabled_still_raises(self):
        """With auto_convert off (default), unit mismatch still raises."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        assert get_auto_convert() is False
        sv = _make_sv()
        with pytest.raises(TypeError, match="not accepted"):
            sv.relative_position_r = 0.7 * u.km

    def test_incompatible_dims_still_raises(self):
        """Even with auto_convert on, wrong dimensions must still raise."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        set_auto_convert(True)
        try:
            sv = _make_sv()
            with pytest.raises(TypeError, match="incompatible"):
                sv.relative_position_r = 10 * u.m / u.s
        finally:
            set_auto_convert(False)

    def test_exact_match_no_conversion(self):
        """Exact match still works with auto_convert on (no unnecessary conversion)."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        set_auto_convert(True)
        try:
            sv = _make_sv()
            sv.relative_position_r = 700 * u.m
            assert sv.relative_position_r.value == pytest.approx(700.0)
            assert sv.relative_position_r.units == LengthUnits.M
        finally:
            set_auto_convert(False)

    def test_toggle_at_runtime(self):
        """Flag can be toggled and takes effect immediately."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        sv = _make_sv()

        # Off → raises
        set_auto_convert(False)
        with pytest.raises(TypeError, match="not accepted"):
            sv.relative_position_r = 0.7 * u.km

        # On → converts
        set_auto_convert(True)
        try:
            sv.relative_position_r = 0.7 * u.km
            assert sv.relative_position_r.value == pytest.approx(700.0)
        finally:
            set_auto_convert(False)

    def test_getter_setter(self):
        """get/set_auto_convert work correctly with type validation."""
        assert get_auto_convert() is False
        set_auto_convert(True)
        assert get_auto_convert() is True
        set_auto_convert(False)
        assert get_auto_convert() is False
        with pytest.raises(TypeError, match="Expected bool"):
            set_auto_convert("yes")  # type: ignore[arg-type]

    def test_construction_with_auto_convert(self):
        """Auto-convert works at construction time too."""
        pint = pytest.importorskip("pint")
        u = pint.UnitRegistry()
        set_auto_convert(True)
        try:
            sv = RelativeStateVectorType(
                relative_position_r=0.7 * u.km,
                relative_position_t=0.8 * u.km,
                relative_position_n=0.9 * u.km,
                relative_velocity_r=10 * u.m / u.s,
                relative_velocity_t=20 * u.m / u.s,
                relative_velocity_n=30 * u.m / u.s,
            )
            assert sv.relative_position_r.value == pytest.approx(700.0)
            assert sv.relative_position_r.units == LengthUnits.M
            assert sv.relative_position_t.value == pytest.approx(800.0)
        finally:
            set_auto_convert(False)
