import pytest
from pydantic import ValidationError
from generator_standard.vocs import ContinuousVariable


def test_continuous_variable_success():
    var = ContinuousVariable(name="x", domain=[0.0, 1.0], default_value=0.5)
    assert var.domain == [0.0, 1.0]
    assert var.default_value == 0.5


def test_continuous_variable_invalid_bounds():
    with pytest.raises(ValidationError):
        ContinuousVariable(name="y", domain=[1.5, 1.0], default_value=0.5)


if __name__ == "__main__":
    pytest.main([__file__])
