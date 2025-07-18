import pytest
from pydantic import ValidationError
from generator_standard.vocs import (
    ContinuousVariable,
    DiscreteVariable,
    VOCS,
    BoundsConstraint,
    GreaterThanConstraint,
    LessThanConstraint,
    ConstraintTypeEnum,
    ObjectiveTypeEnum,
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


def test_invalid_variable_class():
    with pytest.raises(ValueError, match="not available"):
        VOCS(
            variables={"x": {"type": "FakeVariable", "value": 1}},
            objectives={},
        )


def test_invalid_constraint_class():
    with pytest.raises(ValueError, match="not available"):
        VOCS(
            variables={"x": [0.0, 1.0]},
            objectives={},
            constraints={"c": {"type": "FakeConstraint", "value": 1}},
        )


def test_invalid_constraint_list_type():
    with pytest.raises(ValueError, match="must be a string"):
        VOCS(variables={"x": [0.0, 1.0]}, objectives={}, constraints={"c": [[1, 2]]})


def test_invalid_bounds_constraint_short_list():
    with pytest.raises(ValidationError, match="at least 2 items"):
        VOCS(
            variables={"x": [0.0, 1.0]},
            objectives={},
            constraints={"c": ["BOUNDS", 0.0]},
        )


def test_invalid_constraint_type_rejected():
    with pytest.raises(ValueError, match="constraint input type"):
        VOCS(variables={"x": [0.0, 1.0]}, objectives={}, constraints={"c": 5.0})


def test_invalid_non_bounds_constraint_short_list():
    with pytest.raises(ValueError, match="not correctly specified"):
        VOCS(
            variables={"x": [0.0, 1.0]}, objectives={}, constraints={"c": ["LESS_THAN"]}
        )


def test_unsupported_constraint_type():
    with pytest.raises(ValueError, match="not supported"):
        VOCS(
            variables={"x": [0.0, 1.0]},
            objectives={},
            constraints={"c": ["UNSUPPORTED", 1.0]},
        )


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
    vocs = VOCS(
        variables={"x": [0.5, 1.0]},
        objectives={"f": "MINIMIZE"},
        constants={"alpha": 1.0, "beta": 2.0},
        observables=["temp", "temp2"],
    )
    assert isinstance(vocs.variables["x"], ContinuousVariable)
    assert vocs.variables["x"].domain == [0.5, 1.0]
    assert vocs.objectives["f"] == "MINIMIZE"
    assert vocs.constants["alpha"] == 1.0
    assert vocs.constants["beta"] == 2.0
    assert "temp" in vocs.observables
    assert "temp2" in vocs.observables


def test_vocs_1a():
    vocs = VOCS(
        variables={
            "x": [0, 1],  # Defaults to Continuous even if integer bounds
            "y": {"a", "b", "c"},
        },
        objectives={"f": "MINIMIZE"},
    )
    assert isinstance(vocs.variables["x"], ContinuousVariable)
    assert isinstance(vocs.variables["y"], DiscreteVariable)


def check_objectives(vocs):
    expected = {"f": "MINIMIZE", "f2": "MAXIMIZE", "f3": "EXPLORE"}
    for key, val in expected.items():
        assert vocs.objectives[key] == val, (
            f"{key} expected {val}, got {vocs.objectives[key]}"
        )


def test_vocs_2():
    vocs = VOCS(
        variables={
            "x": ContinuousVariable(domain=[0.5, 1.0]),
            "y": DiscreteVariable(values=["a", "b", "c"]),
        },
        objectives={"f": "MINIMIZE", "f2": "MAXIMIZE", "f3": "EXPLORE"},
    )
    check_objectives(vocs)


def test_vocs_2a():
    vocs = VOCS(
        variables={
            "x": ContinuousVariable(domain=[0.5, 1.0]),
        },
        objectives={
            "f": ObjectiveTypeEnum.MINIMIZE,
            "f2": ObjectiveTypeEnum.MAXIMIZE,
            "f3": ObjectiveTypeEnum.EXPLORE,
        },
    )
    check_objectives(vocs)


def test_vocs_2b():
    vocs = VOCS(
        variables={
            "x": ContinuousVariable(domain=[0.5, 1.0]),
        },
        objectives={
            "f": ObjectiveTypeEnum("minimize"),
            "f2": ObjectiveTypeEnum("maximize"),
            "f3": ObjectiveTypeEnum("explore"),
        },
    )
    check_objectives(vocs)


def check_constraints(vocs):
    assert isinstance(vocs.constraints["c"], GreaterThanConstraint)
    assert vocs.constraints["c"].value == 0.0
    assert isinstance(vocs.constraints["c1"], LessThanConstraint)
    assert vocs.constraints["c1"].value == 2.0
    assert isinstance(vocs.constraints["c2"], BoundsConstraint)
    assert vocs.constraints["c2"].range == [-1.0, 1.0]


def test_vocs_3():
    vocs = VOCS(
        variables={"x": [0.5, 1.0]},
        objectives={"f": "MINIMIZE"},
        constraints={
            "c": ["GREATER_THAN", 0.0],
            "c1": ["LESS_THAN", 2.0],
            "c2": ["BOUNDS", -1.0, 1.0],
        },
    )
    check_constraints(vocs)


def test_vocs_3a():
    vocs = VOCS(
        variables={"x": [0.5, 1.0]},
        objectives={"f": "MINIMIZE"},
        constraints={
            "c": GreaterThanConstraint(value=0.0),
            "c1": LessThanConstraint(value=2.0),
            "c2": BoundsConstraint(range=[-1.0, 1.0]),
        },
    )
    check_constraints(vocs)


def test_vocs_3b():
    vocs = VOCS(
        variables={"x": [0.0, 1.0]},
        objectives={"f": "MINIMIZE"},
        constraints={
            "c": [ConstraintTypeEnum("greater_than"), 0.0],
            "c1": [ConstraintTypeEnum("less_than"), 2.0],
            "c2": [ConstraintTypeEnum("bounds"), -1.0, 1.0],
        },
    )
    check_constraints(vocs)


def test_vocs_serialization_deserialization():
    vocs = VOCS(
        variables={
            "x": [0, 1],
            "y": {"a", "b", "c"},
        },
        objectives={"f1": "MINIMIZE", "f2": "MAXIMIZE", "f3": "EXPLORE"},
        constraints={
            "c": ["GREATER_THAN", 0.0],
            "c1": ["LESS_THAN", 2.0],
            "c2": ["BOUNDS", -1.0, 1.0],
        },
    )

    # Serialize to JSON
    model = vocs.model_dump()

    # Deserialize back to VOCS object
    vocs_deserialized = VOCS.model_validate(model)

    # Check if the deserialized object matches the original
    assert vocs_deserialized == vocs
