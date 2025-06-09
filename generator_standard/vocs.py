from enum import Enum
from typing import Any

from pydantic import ConfigDict, conlist, conset, Field, field_validator, model_validator, \
    BaseModel, StrictInt


class BaseVariable(BaseModel):
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
                "Bounds specified do not satisfy the "
                "condition value[1] > value[0]."
            )
        return self


class DiscreteVariable(BaseVariable):
    values: conset(Any, min_length=1) = Field(
        description="List of allowed discrete values"
    )


class IntegerVariable(BaseVariable):
    domain: conlist(int, min_length=2, max_length=2) | None = None

    @model_validator(mode="after")
    def validate_bounds_are_integers(self):
        if self.domain is not None:
            if self.domain[0] >= self.domain[1]:
                raise ValueError("IntegerVariable domain must satisfy domain[0] < domain[1]")
        return self


class BaseConstraint(BaseModel):
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


class ConstraintTypeEnum(str, Enum):
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"
    BOUNDS = "BOUNDS"

    # Allow any case
    @classmethod
    def _missing_(cls, name):
        if isinstance(name, str):
            for member in cls:
                if member.name.lower() == name.lower():
                    return member


class ObjectiveTypeEnum(str, Enum):
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"
    EXPLORE = "EXPLORE"

    # Allow any case
    @classmethod
    def _missing_(cls, name):
        for member in cls:
            if member.name.lower() == name.lower():
                return member


VariableType = ContinuousVariable | DiscreteVariable | IntegerVariable


class VOCS(BaseModel):
    """
    Variables, Objectives, Constraints, and other Settings (VOCS) data structure
    to describe optimization problems.
    """

    variables: dict[str, VariableType]
    objectives: dict[
        str,
        ObjectiveTypeEnum
    ] = Field(
        default={}, description="objective names with type of objective"
    )
    constraints: dict[
        str, BaseConstraint
    ] = Field(
        default={},
        description="constraint names with a list of constraint type and value",
    )
    constants: dict[str, Any] = Field(
        default={}, description="constant names and values passed to evaluate function"
    )
    observables: set[str] = Field(
        default=set(),
        description="observation names tracked alongside objectives and constraints",
    )
    model_config = ConfigDict(
        validate_assignment=True, use_enum_values=True, extra="forbid"
    )

    @field_validator("variables", mode="before")
    def validate_variables(cls, v):
        assert isinstance(v, dict)
        for name, val in v.items():
            if isinstance(val, BaseVariable):
                v[name] = val
            elif isinstance(val, list):
                if len(val) != 2:
                    raise ValueError(f"variable {val} is not correctly specified, must have 2 elements")
                v[name] = ContinuousVariable(domain=val)
            elif isinstance(val, set):
                v[name] = DiscreteVariable(values=val)
            elif isinstance(val, dict):
                variable_type = val.pop("type")
                try:
                    class_ = globals()[variable_type]
                except KeyError:
                    raise ValueError(f"constraint type {variable_type} is not "
                                     f"available")
                v[name] = class_(**val)

            else:
                raise ValueError(f"variable input type {type(val)} not supported")

        return v

    @field_validator("constraints", mode="before")
    def validate_constraints(cls, v):
        assert isinstance(v, dict)
        for name, val in v.items():
            if isinstance(val, BaseConstraint):
                v[name] = val
            elif isinstance(val, dict):
                constraint_type = val.pop("type")
                try:
                    class_ = globals()[constraint_type]
                except KeyError:
                    raise ValueError(f"constraint type {constraint_type} is not "
                                     f"available")
                v[name] = class_(**val)
            elif isinstance(val, list):
                if not isinstance(val[0], str):
                    raise ValueError(f"constraint type {val[0]} must be a string if "
                                     f"specified by a list")

                constraint_type = val[0].upper()
                if constraint_type not in CONSTRAINT_CLASSES:
                    raise ValueError(
                        f"Constraint type '{constraint_type}' is not supported for '{name}'.")

                # Dynamically create the constraint instance
                if constraint_type == "BOUNDS":
                    v[name] = CONSTRAINT_CLASSES[constraint_type](range=val[1:])                  
                else:
                    if len(val) < 2:
                        raise ValueError(f"constraint {val} is not correctly "
                                         "specified")
                    v[name] = CONSTRAINT_CLASSES[constraint_type](value=val[1])

            else:
                raise ValueError(f"constraint input type {type(val)} not supported")

        return v

    @field_validator("objectives", mode="before")
    def validate_objectives(cls, v):
        assert isinstance(v, dict)
        for name, val in v.items():
            if isinstance(val, ObjectiveTypeEnum):
                v[name] = val
            elif isinstance(val, str):
                try:
                    v[name] = ObjectiveTypeEnum(val.upper())
                except ValueError:
                    raise ValueError(
                        f"Objective type '{val}' is not supported for '{name}'."
                    )
            else:
                raise ValueError(f"objective input type {type(val)} not supported")

        return v
