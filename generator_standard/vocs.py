from enum import Enum
from typing import Any, Union, Optional, Tuple

from pydantic import (
    ConfigDict,
    conlist,
    conset,
    Field,
    field_validator,
    model_validator,
    BaseModel,
    field_serializer,
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


class BaseConstant(BaseField):
    value: Any


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


class BaseObjective(BaseField):
    direction: ObjectiveTypeEnum





class VOCS(BaseModel):
    """
    Variables, Objectives, Constraints, and other Settings (VOCS) data structure
    to describe optimization problems.
    """

    variables: dict[str, BaseVariable]
    objectives: dict[str, BaseObjective] = Field(
        default={}, description="objective names with type of objective"
    )
    constraints: dict[str, BaseConstraint] = Field(
        default={},
        description="constraint names with a list of constraint type and value",
    )
    constants: dict[str, BaseConstant] = Field(
        default={}, description="constant names and values passed to evaluate function"
    )
    observables: Union[set[str], dict[str, Any]] = Field(
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
                    raise ValueError(
                        f"variable {val} is not correctly specified, must have 2 elements"
                    )
                v[name] = ContinuousVariable(domain=val)
            elif isinstance(val, set):
                v[name] = DiscreteVariable(values=val)
            elif isinstance(val, dict):
                variable_type = val.pop("type")
                try:
                    class_ = globals()[variable_type]
                except KeyError:
                    raise ValueError(
                        f"variable type {variable_type} is not available"
                    )
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
                    raise ValueError(
                        f"constraint type {constraint_type} is not available"
                    )
                v[name] = class_(**val)
            elif isinstance(val, list):
                if not isinstance(val[0], str):
                    raise ValueError(
                        f"constraint type {val[0]} must be a string if "
                        f"specified by a list"
                    )

                constraint_type = val[0].upper()
                if constraint_type not in CONSTRAINT_CLASSES:
                    raise ValueError(
                        f"Constraint type '{constraint_type}' is not supported for '{name}'."
                    )

                # Dynamically create the constraint instance
                if constraint_type == "BOUNDS":
                    v[name] = CONSTRAINT_CLASSES[constraint_type](range=val[1:])
                else:
                    if len(val) < 2:
                        raise ValueError(f"constraint {val} is not correctly specified")
                    v[name] = CONSTRAINT_CLASSES[constraint_type](value=val[1])

            else:
                raise ValueError(f"constraint input type {type(val)} not supported")

        return v

    @field_validator("objectives", mode="before")
    def validate_objectives(cls, v):
        assert isinstance(v, dict)
        for name, val in v.items():
            if isinstance(val, BaseObjective):
                v[name] = val
            elif isinstance(val, ObjectiveTypeEnum):
                v[name] = BaseObjective(direction=val)
            elif isinstance(val, str):
                try:
                    v[name] = BaseObjective(direction=ObjectiveTypeEnum(val.upper()))
                except ValueError:
                    raise ValueError(
                        f"Objective type '{val}' is not supported for '{name}'."
                    )
            elif isinstance(val, dict):
                # Handle deserialized BaseObjective
                if "type" in val and val["type"] == "BaseObjective":
                    v[name] = BaseObjective(**val)
                else:
                    raise ValueError(f"objective {val} is not correctly specified")
            else:
                raise ValueError(f"objective input type {type(val)} not supported")
        return v

    @field_validator("constants", mode="before")
    def validate_constants(cls, v):
        assert isinstance(v, dict)
        for name, val in v.items():
            if isinstance(val, BaseConstant):
                v[name] = val
            elif isinstance(val, dict):
                constant_type = val.pop("type")
                try:
                    class_ = globals()[constant_type]
                except KeyError:
                    raise ValueError(
                        f"constant type {constant_type} is not available"
                    )
                v[name] = class_(**val)
            else:
                # For backward compatibility, wrap raw values in BaseConstant
                v[name] = BaseConstant(value=val)
        return v

    @field_validator("observables", mode="before")
    def validate_observables(cls, v):
        if isinstance(v, (set, list)):
            return set(v) if isinstance(v, list) else v
        elif isinstance(v, dict):
            return v
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
        if isinstance(v, set):
            return list(v)
        elif isinstance(v, dict):
            return v
        return v
