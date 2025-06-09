import pytest
from pydantic import ValidationError
from generator_standard.vocs import (
    ContinuousVariable, DiscreteVariable, IntegerVariable, VOCS, BoundsConstraint
)


def test_continuous_variable_success():
    var = ContinuousVariable(domain=[0.0, 1.0], default_value=0.5)
    assert var.domain == [0.0, 1.0]
    assert var.default_value == 0.5


def test_continuous_variable_invalid_bounds():
    with pytest.raises(ValidationError):
        ContinuousVariable(domain=[1.5, 1.0], default_value=0.5)


def test_discrete_variable_success():
    d = DiscreteVariable(values={1, 2, 3})
    assert d.values == {1, 2, 3}


def test_discrete_variable_strings():
    d = DiscreteVariable(values={"a", "bb", "ccc"})
    assert d.values == {"a", "bb", "ccc"}


def test_discrete_variable_empty_fail():
    with pytest.raises(ValidationError):
        DiscreteVariable(values=[])


def test_invalid_continuous_bounds_list():
    with pytest.raises(ValueError, match="must have 2 elements"):
        VOCS(variables={"x": [0.5]}, objectives={})


def test_discrete_variable_removes_duplicates():
    d = DiscreteVariable(values=["a", "a", "b"])
    assert d.values == {"a", "b"}


def test_invalid_variable_dict_type():
    with pytest.raises(ValueError, match="not supported"):
        VOCS(variables={"x": 5.0}, objectives={})


def test_invalid_constraint_class():
    with pytest.raises(ValueError, match="not available"):
        VOCS(variables={"x": [0.0, 1.0]},
             objectives={},
             constraints={"c": {"type": "FakeConstraint", "value": 1}})


def test_invalid_constraint_list_type():
    with pytest.raises(ValueError, match="must be a string"):
        VOCS(variables={"x": [0.0, 1.0]},
             objectives={},
             constraints={"c": [[1, 2]]})


def test_invalid_bounds_constraint_short_list():
    with pytest.raises(ValidationError, match="at least 2 items"):
        VOCS(variables={"x": [0.0, 1.0]},
             objectives={},
             constraints={"c": ["BOUNDS", 0.0]})


def test_invalid_constraint_type_rejected():
    with pytest.raises(ValueError, match="constraint input type"):
        VOCS(
            variables={"x": [0.0, 1.0]},
            objectives={},
            constraints={"c": 5.0}
        )


def test_invalid_non_bounds_constraint_short_list():
    with pytest.raises(ValueError, match="not correctly specified"):
        VOCS(variables={"x": [0.0, 1.0]},
             objectives={},
             constraints={"c": ["LESS_THAN"]})


def test_unsupported_constraint_type():
    with pytest.raises(ValueError, match="not supported"):
        VOCS(variables={"x": [0.0, 1.0]},
             objectives={},
             constraints={"c": ["UNSUPPORTED", 1.0]})


def test_objective_enum_case_insensitive():
    vocs = VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": "minimize"})
    assert vocs.objectives["f"] == "MINIMIZE"


def test_invalid_objective_enum_value():
    with pytest.raises(ValueError, match="Objective type 'bad' is not supported"):
        VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": "bad"})


def test_invalid_objective_type():
    with pytest.raises(ValueError, match="objective input type"):
        VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": 5})


def test_bounds_constraint_invalid_range_order():
    with pytest.raises(ValueError, match="ascending order"):
        BoundsConstraint(range=[1.0, 0.0])


def test_vocs_1():
    _ = VOCS(
        variables={"x":[0.5, 1.0]},
        objectives={"f": "MINIMIZE"},
        constants={"alpha": 1.0},
        observables=["temp"]
    )


def test_vocs_1a():
    _ = VOCS(
        variables={"x": [0.5, 1.0],
                   "y": {"a", "b", "c"}},
        objectives={"f": "MINIMIZE"},
        constants={"alpha": 1.0},
        observables=["temp"]
    )


def test_vocs_2():
    _ = VOCS(
        variables={
            "x": ContinuousVariable(domain=[0.5, 1.0]),
            "y": DiscreteVariable(values=["a", "b", "c"]),
            "z": IntegerVariable(domain=[1, 10]),
        },
        objectives={"f": "MINIMIZE",
                    "f2": "MAXIMIZE"},
        constants={"alpha": 1.0,
                   "beta": 2.0},
        observables=["temp", "temp2"]
    )


def test_vocs_2a():
    _ = VOCS(
        variables={
            "x": [0.5, 1.0],
            "y": {"a", "b", "c"}
        },
        objectives={"f": "MINIMIZE",
                    "f2": "MAXIMIZE"},
        constants={"alpha": 1.0,
                   "beta": 2.0},
        observables=["temp", "temp2"]
    )


def test_vocs_3():
    _ = VOCS(
        variables={"x": [0.5, 1.0]},
        objectives={"f": "MINIMIZE"},
        constraints={"c": ["GREATER_THAN", 0.0],
                     "c1": ["LESS_THAN", 2.0],
                     "c2": ["LESS_than", 3.0]},
        constants={"alpha": 1.0},
        observables=["temp"]
    )
