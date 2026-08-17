from decimal import Decimal

import pytest

from modeling.units import UnitError, compatible, convert


def test_units_convert_with_explicit_dimensions():
    assert convert(1, "kg", "g") == Decimal("1000")
    assert compatible("hour", "minute")
    assert not compatible("kg", "Bs")


def test_units_reject_incompatible_conversion():
    with pytest.raises(UnitError):
        convert(1, "kg", "Bs")
