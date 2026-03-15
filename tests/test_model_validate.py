# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
Tests for the validation exceptions on xsdata model classes.
"""

import pytest

# Importing model_validate triggers patching
import ccsds_ndm.model_validate  # noqa: F401

# ndmxml2 imports
from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_common_2_0 import LengthType
from tests.shared_validate_tests import (
    SharedTestCorrectWrapperPasses,
    SharedTestErrorMessageFormat,
    SharedTestNdmxml4,
    SharedTestRejectPlainNumbers,
    SharedTestRoundTrip,
    _make_sv,
)


class TestRejectPlainNumbers(SharedTestRejectPlainNumbers):
    """Assigning plain numbers to wrapper-typed fields must raise TypeError."""


class TestCorrectWrapperPasses(SharedTestCorrectWrapperPasses):
    """Correct wrapper types and None must pass through."""


class TestErrorMessageFormat(SharedTestErrorMessageFormat):
    """Error messages must include field name, class name, and expected type."""


class TestNdmxml4(SharedTestNdmxml4):
    """Verify validation works with ndmxml4 Uo/Ur variant types."""


class TestRoundTrip(SharedTestRoundTrip):
    """Validation must not break KVN/XML serialization."""


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
