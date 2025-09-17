from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, field_serializer

from pydantic import (
    conlist,
    conset,
    Field,
    field_validator,
    model_validator,
    BaseModel,
)


class BaseField(BaseModel):
    dtype: Optional[str] = None


class BaseVariable(BaseField):
    default_value: float | None = None


class ContinuousVariable(BaseVariable):
    domain: conlist(float, min_length=2, max_length=2) = Field(
        description="domain of the variable, [min, max]"
    )

    @model_validator(mode="after")
    def validate_bounds(self):
        # check to make sure bounds are correct
        if not self.domain[1] > self.domain[0]:
            raise ValueError(
                "Bounds specified do not satisfy the condition value[1] > value[0]."
            )
        return self


class DiscreteVariable(BaseVariable):
    values: conset(Any, min_length=1) = Field(
        description="List of allowed discrete values"
    )


class ValidatedDict(dict, ABC):
    def __init__(self, *args, **kwargs):
        raw = dict(*args, **kwargs)  # collect initial data
        super().__init__()  # start with empty dict
        for k, v in raw.items():
            self[k] = v  # <- goes through __setitem__, runs validation

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value  # will trigger __setitem__

    def __setitem__(self, key, value):
        """update dict item to do validation on set"""
        value = self._validate_entry(key, value)
        super().__setitem__(key, value)

    @staticmethod
    @abstractmethod
    def _validate_entry(name, value):
        ...


class VariableDict(ValidatedDict):
    @staticmethod
    def _validate_entry(name, val):
        if isinstance(val, BaseVariable):
            return val
        elif isinstance(val, list):
            if len(val) != 2:
                raise ValueError(
                    f"variable {name} is not correctly specified, must have two elements representing upper and lower bounds."
                )
            return ContinuousVariable(domain=val)
        elif isinstance(val, set):
            return DiscreteVariable(values=val)
        elif isinstance(val, dict):
            if "type" not in val:
                raise ValueError(f"variable {name} must provide type field")
            variable_type = val.pop("type")
            try:
                class_ = globals()[variable_type]
            except KeyError:
                raise ValueError(f"variable type {variable_type} is not available")
            return class_(**val)
        else:
            raise ValueError(
                f"variable {name}: input type {type(val)} not supported. "
                "Must be a BaseVariable, list[2], set, or dict with type field."
            )


class BaseConstraint(BaseField):
    pass


class LessThanConstraint(BaseConstraint):
    value: float

    def check(self, x: float) -> bool:
        return x < self.value


class GreaterThanConstraint(BaseConstraint):
    value: float

    def check(self, x: float) -> bool:
        return x > self.value


class BoundsConstraint(BaseConstraint):
    range: conlist(float, min_length=2, max_length=2) = Field(
        description="range of the constraint [min, max]"
    )

    @field_validator("range")
    def validate_range(cls, value):
        if len(value) != 2 or value[0] >= value[1]:
            raise ValueError("'range' must have two numbers in ascending order.")
        return value

    def check(self, x: float) -> bool:
        lo, hi = self.range
        return lo <= x <= hi  # open both ends


CONSTRAINT_CLASSES = {
    "LESS_THAN": LessThanConstraint,
    "GREATER_THAN": GreaterThanConstraint,
    "BOUNDS": BoundsConstraint,
}


class ConstraintDict(ValidatedDict):
    @staticmethod
    def _validate_entry(name, val):
        if isinstance(val, BaseConstraint):
            return val
        elif isinstance(val, dict):
            if "type" not in val:
                raise ValueError(f"constraint {name} must provide type field")
            constraint_type = val.pop("type")
            try:
                class_ = globals()[constraint_type]
            except KeyError:
                raise ValueError(f"constraint type {constraint_type} is not available")
            return class_(**val)
        elif isinstance(val, list):
            if not isinstance(val[0], str):
                raise ValueError(
                    f"constraint type {val[0]} must be a string if specified by a list"
                )

            constraint_type = val[0].upper()
            if constraint_type not in CONSTRAINT_CLASSES:
                raise ValueError(
                    f"Constraint type '{constraint_type}' is not supported for '{name}'."
                )

            # Dynamically create the constraint instance
            if constraint_type == "BOUNDS":
                return CONSTRAINT_CLASSES[constraint_type](range=val[1:])
            else:
                if len(val) < 2:
                    raise ValueError(f"constraint {val} is not correctly specified")
                return CONSTRAINT_CLASSES[constraint_type](value=val[1])

        else:
            raise ValueError(f"constraint input type {type(val)} not supported")


class BaseObjective(BaseField):
    pass


class MinimizeObjective(BaseObjective):
    pass


class MaximizeObjective(BaseObjective):
    pass


class ExploreObjective(BaseObjective):
    pass


OBJECTIVE_CLASSES = {
    "MINIMIZE": MinimizeObjective,
    "MAXIMIZE": MaximizeObjective,
    "EXPLORE": ExploreObjective,
}


class ObjectiveDict(ValidatedDict):
    @staticmethod
    def _validate_entry(name, val):
        if isinstance(val, BaseObjective):
            return val
        elif isinstance(val, dict):
            if "type" not in val:
                raise ValueError(f"objective {name} is not correctly specified")
            objective_type = val.pop("type")
            try:
                class_ = globals()[objective_type]
                if not issubclass(class_, BaseObjective):
                    raise ValueError(
                        f"objective type {objective_type} is not a valid objective"
                    )
            except KeyError:
                raise ValueError(f"objective type {objective_type} is not available")
            return class_(**val)
        elif isinstance(val, str):
            try:
                return OBJECTIVE_CLASSES[val.upper()]()
            except KeyError:
                raise ValueError(
                    f"Objective type '{val}' is not supported for '{name}'."
                )
        else:
            raise ValueError(f"objective input type {type(val)} not supported")


class Constant(BaseField):
    value: Any


class ConstantDict(ValidatedDict):
    @staticmethod
    def _validate_entry(name, val):
        if isinstance(val, Constant):
            return val
        elif isinstance(val, dict):
            if "type" not in val:
                raise ValueError(f"constant {name} is not correctly specified")
            constant_type = val.pop("type")

            # we only have one constant type for now
            if constant_type != "Constant":
                raise ValueError(
                    f"constant type {constant_type} is not a valid constant"
                )

            return Constant(**val)
        else:
            return Constant(value=val)


class Observable(BaseField):
    pass


class ObservableDict(ValidatedDict):
    @staticmethod
    def _validate_entry(name, val):
        if isinstance(val, Observable):
            return val
        elif isinstance(val, dict):
            if "type" not in val:
                raise ValueError(f"observable {name} is not correctly specified")
            observable_type = val.pop("type")

            # we only have one observable type for now
            if observable_type != "Observable":
                raise ValueError(
                    f"observable type {observable_type} is not a valid observable"
                )

            return Observable(**val)
        elif isinstance(val, str):
            return Observable(dtype=val)
        else:
            raise ValueError(f"observable input type {type(val)} not supported")


class VOCS(BaseModel, validate_assignment=True, arbitrary_types_allowed=True):
    """

    Variables, Objectives, Constraints, and other Settings (VOCS) data structure
    to describe optimization problems.

    .. tab-set::

        .. tab-item:: variables

            Names and settings for input parameters for passing to an objective
            function to solve the optimization problem.

            A **dictionary** with **keys** being variable names (as strings) and **values** as either:

                - A two-element list, representing bounds.
                - A set of discrete values, with curly-braces.
                - A single integer.

            .. code-block:: python
                :linenos:

                from generator_standard.vocs import VOCS

                vocs = VOCS(variables={"x": [0.0, 1.0]})
                ...
                vocs = VOCS(variables={"x": {0, 1, 2, "/usr", "/home", "/bin"}})
                ...
                vocs = VOCS(variables={"x": 32})


        .. tab-item:: objectives

            Names of objective function outputs, and guidance for the direction of optimization.

            A **dictionary** with **keys** being objective names (as strings) and **values** as either:

                - ``"MINIMIZE"``
                - ``"MAXIMIZE"``
                - ``"EXPLORE"``

            .. code-block:: python
                :linenos:

                from generator_standard.vocs import VOCS

                vocs = VOCS(objectives={"f": "MINIMIZE"})
                ...
                vocs = VOCS(objectives={"f": "MAXIMIZE"})
                ...
                vocs = VOCS(objectives={"f": "EXPLORE"})


        .. tab-item:: constraints

            Names of function outputs that and their category of constraint that must be satisfied for
            a valid solution to the optimization problem.

            A **dictionary** with **keys** being constraint names (as strings) and **values** as a length-2 list
            with the first element being ``"LESS_THAN"``, ``"GREATER_THAN"``, or ``"BOUNDS"``.

            The second element depends on the type of constraint:
                - If ``"BOUNDS"``, a two-element list of floats, representing boundaries.
                - If ``"LESS_THAN"``, or ``"GREATER_THAN"``, a single float value.

            .. code-block:: python
                :linenos:

                from generator_standard.vocs import VOCS

                vocs = VOCS(constraints={"c": ["LESS_THAN", 1.0]})
                ...
                vocs = VOCS(constraints={"c": ["GREATER_THAN", 0.0]})
                ...
                vocs = VOCS(constraints={"c": ["BOUNDS", [0.0, 1.0]]})


        .. tab-item:: constants

            Names and values of constants for passing alongside `variables` to the objective function.

            A **dictionary** with **keys** being constant names (as strings) and **values** as any type.

            .. code-block:: python
                :linenos:

                from generator_standard.vocs import VOCS

                vocs = VOCS(constants={"alpha": 1.0, "beta": 2.0})

        .. tab-item:: observables

            Names of other objective function outputs that will be passed
            to the optimizer (alongside the `objectives` and `constraints`).

            A **set** of strings or a **dictionary** with **keys** being names and **values** being type:

            .. code-block:: python
                :linenos:

                from generator_standard.vocs import VOCS

                vocs = VOCS(observables={"temp", "temp2"})
                ...
                vocs = VOCS(observables={"temp": "float", "temp2": "int"})

    """

    variables: VariableDict
    objectives: ObjectiveDict = Field(
        default=ObjectiveDict(), description="objective names with type of objective"
    )
    constraints: ConstraintDict = Field(
        default=ConstraintDict(),
        description="constraint names with a list of constraint type and value",
    )
    constants: ConstantDict = Field(
        default=ConstantDict(),
        description="constant names and values passed to evaluate function",
    )
    observables: ObservableDict = Field(
        default=ObservableDict(),
        description="observables tracked alongside objectives and constraints",
    )
    model_config = ConfigDict(
        validate_assignment=True, use_enum_values=True, extra="forbid"
    )

    @field_validator("variables", mode="before")
    def validate_variables(cls, v):
        return VariableDict(v)

    @field_validator("constraints", mode="before")
    def validate_constraints(cls, v):
        return ConstraintDict(v)

    @field_validator("objectives", mode="before")
    def validate_objectives(cls, v):
        return ObjectiveDict(v)

    @field_validator("constants", mode="before")
    def validate_constants(cls, v):
        return ConstantDict(v)

    @field_validator("observables", mode="before")
    def validate_observables(cls, v):
        # allow a set/list of names for convenience
        if isinstance(v, set) or isinstance(v, list):
            return ObservableDict({name: Observable() for name in v})
        elif isinstance(v, dict):
            return ObservableDict(v)
        else:
            raise ValueError(f"observables input type {type(v)} not supported")

    @field_serializer("variables", "constraints", "objectives", "constants")
    def serialize_objects(self, v):
        output = {}
        for name, val in v.items():
            output[name] = val.model_dump() | {"type": type(val).__name__}
        return output

    @field_serializer("observables")
    def serialize_observables(self, v):
        output = {}
        for name, val in v.items():
            output[name] = val.model_dump() | {"type": type(val).__name__}
        return output

    @property
    def bounds(self) -> list:
        return [v.domain for _, v in self.variables.items()]

    @property
    def variable_names(self) -> list[str]:
        return list(self.variables.keys())

    @property
    def objective_names(self) -> list[str]:
        return list(self.objectives.keys())

    @property
    def constraint_names(self) -> list[str]:
        return list(self.constraints.keys())

    @property
    def observable_names(self) -> list[str]:
        return list(self.observables.keys())

    @property
    def output_names(self) -> list[str]:
        full_list = self.objective_names
        for ele in self.constraint_names:
            if ele not in full_list:
                full_list += [ele]

        for ele in self.observable_names:
            if ele not in full_list:
                full_list += [ele]

        return full_list

    @property
    def constant_names(self) -> list[str]:
        return list(self.constants.keys())

    @property
    def all_names(self) -> list[str]:
        return self.variable_names + self.constant_names + self.output_names

    @property
    def n_variables(self) -> int:
        return len(self.variables)

    @property
    def n_constants(self) -> int:
        return len(self.constants)

    @property
    def n_inputs(self) -> int:
        return self.n_variables + self.n_constants

    @property
    def n_objectives(self) -> int:
        return len(self.objectives)

    @property
    def n_constraints(self) -> int:
        return len(self.constraints)

    @property
    def n_observables(self) -> int:
        return len(self.observables)

    @property
    def n_outputs(self) -> int:
        return len(self.output_names)
