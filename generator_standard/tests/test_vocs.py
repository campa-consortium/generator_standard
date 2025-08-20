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
    MinimizeObjective,
    MaximizeObjective,
    ExploreObjective,
    Observable,
    Constant,
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
    with pytest.raises(ValueError, match="must have two elements"):
        VOCS(variables={"x": [0.5]}, objectives={})


def test_discrete_variable_removes_duplicates():
    d = DiscreteVariable(values=["a", "a", "b"])
    assert d.values == {"a", "b"}


def test_invalid_variable_dict_type():
    with pytest.raises(ValidationError, match="not supported"):
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

def test_adding_variables():
    v = VOCS(variables={"x": [0.0, 1.0]}, objectives={})
    v.variables["y"] = [0.0, 2.0]
    assert isinstance(v.variables["y"], ContinuousVariable)
    assert v.variables["y"].domain == [0.0, 2.0]

    with pytest.raises(ValueError, match="not supported"):
        v.variables["z"] = 5.0

def test_adding_constraints():
    v = VOCS(variables={"x": [0.0, 1.0]}, objectives={})
    v.constraints["c"] = ["LESS_THAN", 0.0]
    assert isinstance(v.constraints["c"], LessThanConstraint)
    assert v.constraints["c"].value == 0.0

    with pytest.raises(ValueError, match="not supported"):
        v.constraints["c2"] = 5.0

def test_unsupported_constraint_type():
    with pytest.raises(ValueError, match="not supported"):
        VOCS(
            variables={"x": [0.0, 1.0]},
            objectives={},
            constraints={"c": ["UNSUPPORTED", 1.0]},
        )


def test_objective_enum_case_insensitive():
    vocs = VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": "minimize"})
    assert isinstance(vocs.objectives["f"], MinimizeObjective)


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
    assert isinstance(vocs.objectives["f"], MinimizeObjective)
    assert vocs.constants["alpha"].value == 1.0
    assert vocs.constants["beta"].value == 2.0
    assert "temp" in vocs.observables
    assert "temp2" in vocs.observables


def test_vocs_1a():
    vocs = VOCS(
        variables={
            "x": [0, 1],  # Defaults to Continuous even if integer bounds
            "y": {"a", "b", "c"},
        },
        objectives={"f": "MINIMIZE"},
        # observables={"temp": "float", "temp_array": (float, (2, 4))},
        observables={"temp": "float"},
    )
    assert isinstance(vocs.variables["x"], ContinuousVariable)
    assert isinstance(vocs.variables["y"], DiscreteVariable)
    assert isinstance(vocs.observables["temp"], Observable)
    assert vocs.observables["temp"].dtype == "float"
    # assert isinstance(vocs.observables["temp_array"], Observable)
    # assert vocs.observables["temp_array"].dtype == (float, (2, 4))


def check_objectives(vocs):
    expected = {"f": MinimizeObjective, "f2": MaximizeObjective, "f3": ExploreObjective}
    for key, val in expected.items():
        assert isinstance(vocs.objectives[key], val), (
            f"{key} expected {val}, got {type(vocs.objectives[key])}"
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
        # observables=["temp"],
        observables={"temp": "float", "temp2": "int"},        
    )

    # Serialize to JSON
    model = vocs.model_dump()

    # Deserialize back to VOCS object
    vocs_deserialized = VOCS.model_validate(model)

    # Check if the deserialized object matches the original
    assert vocs_deserialized == vocs


def test_vocs_set_observables_serialization():
    vocs = VOCS(
        variables={"x": [0, 1]},
        observables={"temp", "temp2"}
    )
    model = vocs.model_dump()
    vocs_deserialized = VOCS.model_validate(model)
    assert vocs_deserialized == vocs


def test_vocs_observable_object_input():
    vocs = VOCS(
        variables={"x": [0, 1]},
        observables={"temp": Observable(dtype="float")}
    )
    assert isinstance(vocs.observables["temp"], Observable)
    assert vocs.observables["temp"].dtype == "float"


def test_invalid_observables_input():
    with pytest.raises(ValueError, match="observables input type"):
        VOCS(
            variables={"x": [0, 1]},
            observables=123  # invalid type
        )


def test_objective_object_input():
    vocs = VOCS(
        variables={"x": [0, 1]},
        objectives={"f": MinimizeObjective()}
    )
    assert isinstance(vocs.objectives["f"], MinimizeObjective)


def test_objective_dict_with_invalid_type():
    with pytest.raises(ValueError, match="not available"):
        VOCS(
            variables={"x": [0, 1]},
            objectives={"f": {"type": "InvalidObjective"}}
        )


def test_objective_dict_missing_type():
    with pytest.raises(ValueError, match="not correctly specified"):
        VOCS(
            variables={"x": [0, 1]},
            objectives={"f": {"some_field": "value"}}
        )


def test_objective_invalid_input_type():
    with pytest.raises(ValueError, match="not supported"):
        VOCS(
            variables={"x": [0, 1]},
            objectives={"f": 123}
        )


def test_constant_object_input():
    vocs = VOCS(
        variables={"x": [0, 1]},
        constants={"c": Constant(value=5)}
    )
    assert isinstance(vocs.constants["c"], Constant)


def test_constant_dict_with_invalid_type():
    with pytest.raises(ValueError, match="not available"):
        VOCS(
            variables={"x": [0, 1]},
            constants={"c": {"type": "InvalidConstant", "value": 5}}
        )


def test_objective_dict_with_non_objective_class():
    with pytest.raises(ValueError, match="not available"):
        VOCS(
            variables={"x": [0, 1]},
            objectives={"f": {"type": "Constant"}}  # Valid class but not BaseObjective
        )


def test_constant_dict_construction():
    vocs = VOCS(
        variables={"x": [0, 1]},
        constants={"c": {"type": "Constant", "value": 42}}
    )
    assert isinstance(vocs.constants["c"], Constant)
    assert vocs.constants["c"].value == 42
    

def test_bounds_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]})
    assert vocs.bounds == [[0, 1], [2, 4]]


def test_variable_names_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]})
    assert vocs.variable_names == ["x", "y"]


def test_objective_names_property():
    vocs = VOCS(
        variables={"x": [0, 1], "y": [2, 4]},
        objectives={"f1": "MINIMIZE", "f2": "MAXIMIZE", "f3": "EXPLORE"},
    )
    assert vocs.objective_names == ["f1", "f2", "f3"]


def test_constraint_names_property():
    vocs = VOCS(
        variables={"x": [0, 1], "y": [2, 4]},
        constraints={
            "c1": ["GREATER_THAN", 0.0],
            "c2": ["LESS_THAN", 2.0],
            "c3": ["BOUNDS", -1.0, 1.0],
        },
    )
    assert vocs.constraint_names == ["c1", "c2", "c3"]

    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]})
    assert vocs.constraint_names == []


def test_output_names_property():
    vocs = VOCS(
        variables={"x": [0, 1], "y": [2, 4]},
        objectives={"f1": "MINIMIZE"},
        constraints={
            "c1": ["GREATER_THAN", 0.0],
            "c2": ["LESS_THAN", 2.0],
            "c3": ["BOUNDS", -1.0, 1.0],
        },
        observables=["temp"],
    )
    assert vocs.output_names == ["f1", "c1", "c2", "c3", "temp"]


def test_constant_names_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]}, constants={"alpha": 1.0})
    assert vocs.constant_names == ["alpha"]

    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]})
    assert vocs.constant_names == []


def test_all_names_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]}, constants={"alpha": 1.0})
    assert vocs.all_names == ["x", "y", "alpha"]


def test_n_variables_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]})
    assert vocs.n_variables == 2


def test_n_constants_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]}, constants={"alpha": 1.0})
    assert vocs.n_constants == 1


def test_n_inputs_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]}, constants={"alpha": 1.0})
    assert vocs.n_inputs == 3


def test_n_objectives_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]}, objectives={"f1": "MINIMIZE"})
    assert vocs.n_objectives == 1


def test_n_constraints_property():
    vocs = VOCS(
        variables={"x": [0, 1], "y": [2, 4]},
        constraints={
            "c1": ["GREATER_THAN", 0.0],
            "c2": ["LESS_THAN", 2.0],
            "c3": ["BOUNDS", -1.0, 1.0],
        },
    )
    assert vocs.n_constraints == 3


def test_n_observables_property():
    vocs = VOCS(variables={"x": [0, 1], "y": [2, 4]}, observables=["temp"])
    assert vocs.n_observables == 1


def test_n_outputs_property():
    vocs = VOCS(
        variables={"x": [0, 1], "y": [2, 4]},
        objectives={"f1": "MINIMIZE"},
        constraints={
            "c1": ["GREATER_THAN", 0.0],
            "c2": ["LESS_THAN", 2.0],
            "c3": ["BOUNDS", -1.0, 1.0],
        },
        observables=["temp"],
    )
    assert vocs.n_outputs == 5
