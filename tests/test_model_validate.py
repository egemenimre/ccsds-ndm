# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
Tests for the validation exceptions on xsdata model classes.
"""

from decimal import Decimal
from pathlib import Path

import pytest

# Importing model_validate triggers patching
import ccsds_ndm.model_validate  # noqa: F401

# ndmxml2 imports
from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_cdm_1_0 import (
    DvType,
    DvUnits,
    RelativeMetadataData,
    RelativeStateVectorType,
)
from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_common_2_0 import (
    LengthType,
    LengthUnits,
)

# ndmxml4 imports
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_cdm_1_0 import DvType as DvType4
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_cdm_1_0 import DvUnits as DvUnits4
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_cdm_1_0 import (
    RelativeStateVectorType as RelativeStateVectorType4,
)
from ccsds_ndm.models.ndmxml4.ndmxml_4_0_0_common_4_0 import (
    LengthTypeUo,
)
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


# ---- ndmxml4 tests ----


class TestNdmxml4:
    """Verify validation works with ndmxml4 Uo/Ur variant types."""

    def test_plain_int_raises(self):
        sv = _make_sv4()
        with pytest.raises(TypeError, match="expects LengthTypeUo"):
            sv.relative_position_r = 700  # type: ignore[assignment]

    def test_correct_wrapper_passes(self):
        sv = _make_sv4()
        new_val = LengthTypeUo(value=999, units=LengthUnits4.M)
        sv.relative_position_r = new_val
        assert sv.relative_position_r is new_val


# ---- Idempotency ----


class TestIdempotency:
    """Importing model_validate twice must not break anything."""

    def test_double_import(self):
        import importlib

        importlib.reload(ccsds_ndm.model_validate)
        sv = _make_sv()
        assert isinstance(sv.relative_position_r, LengthType)
        # Still validates
        with pytest.raises(TypeError):
            sv.relative_position_r = 700  # type: ignore[assignment]


# ---- Round-trip I/O ----


class TestRoundTrip:
    """Validation must not break KVN/XML serialization."""

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
