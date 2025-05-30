import pytest
from pydantic import ValidationError
from generator_standard.vocs import (
    ContinuousVariable, DiscreteVariable, IntegerVariable, VOCS
)


def test_vocs_1():
    vocs = VOCS(
        variables={
            "x": ContinuousVariable(domain=[0.5, 1.0])
        },
        objectives={"f": "MINIMIZE"},
        constants={"alpha": 1.0},
        observables=["temp"]
    )


def test_continuous_variable_success():
    var = ContinuousVariable(domain=[0.0, 1.0], default_value=0.5)
    assert var.domain == [0.0, 1.0]
    assert var.default_value == 0.5


def test_continuous_variable_invalid_bounds():
    with pytest.raises(ValidationError):
        ContinuousVariable(domain=[1.5, 1.0], default_value=0.5)


def test_discrete_variable_success():
    d = DiscreteVariable(values=[1.0, 2.0, 3.0])
    assert d.values == [1.0, 2.0, 3.0]


def test_discrete_variable_duplicate_fail():
    with pytest.raises(ValidationError):
        DiscreteVariable(values=[1.0, 2.0, 2.0])


def test_discrete_variable_empty_fail():
    with pytest.raises(ValidationError):
        DiscreteVariable(values=[])


def test_integer_variable_success():
    i = IntegerVariable(value=3)
    assert i.value == 3


def test_integer_variable_rejects_float():
    with pytest.raises(ValidationError):
        IntegerVariable(value=3.0)


def test_integer_variable_str_fail():
    with pytest.raises(ValidationError):
        IntegerVariable(value="foo")


if __name__ == "__main__":
    pytest.main([__file__])
