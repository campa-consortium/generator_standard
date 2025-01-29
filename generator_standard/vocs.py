from enum import Enum
from typing import Any, Dict, List, Union, Optional, Tuple

from pydantic import ConfigDict, conlist, Field, field_validator, model_validator, \
    BaseModel


# Enums for objectives and constraints
class ObjectiveEnum(str, Enum):
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"
    EXPLORE = "EXPLORE"

    # Allow any case
    @classmethod
    def _missing_(cls, name):
        for member in cls:
            if member.name.lower() == name.lower():
                return member


class ConstraintEnum(str, Enum):
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"

    # Allow any case
    @classmethod
    def _missing_(cls, name):
        if isinstance(name, str):
            for member in cls:
                if member.name.lower() == name.lower():
                    return member


class BaseVariable(BaseModel):
    default_value: Optional[float] = None


class DiscreteVariable(BaseVariable):
    values: Tuple[float, ...]

    @model_validator(mode="after")
    def validate_values(self):
        # check to make sure all values are unqiue
        if not len(self.values) == len(set(self.values)):
            raise ValueError("value tuple must have all unique elements")
        return self


class ContinuousVariable(BaseVariable):
    domain: conlist(float, min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_bounds(self):
        # check to make sure bounds are correct
        if not self.domain[1] > self.domain[0]:
            raise ValueError(
                f"Bounds specified for {self.name} do not satisfy the "
                f"condition value[1] > value[0]."
            )
        return self


class FidelityVariable(ContinuousVariable):
    domain: conlist(float, min_length=2, max_length=2) = [0, 1]


class BaseConstraint(BaseModel):
    pass


class LessThanConstraint(BaseConstraint):
    value: float


class GreaterThanConstraint(BaseConstraint):
    value: float


class BoundsConstraint(BaseConstraint):
    range: List[float]

    @field_validator("range")
    def validate_range(cls, value):
        if len(value) != 2 or value[0] >= value[1]:
            raise ValueError("'range' must have two numbers in ascending order.")
        return value


CONSTRAINT_CLASSES = {
    "LESS_THAN": LessThanConstraint,
    "GREATER_THAN": GreaterThanConstraint,
    "BOUNDS": BoundsConstraint,
}


# Base Objective Model
class BaseObjective(BaseModel):
    pass


class MinimizeObjective(BaseObjective):
    pass


class MaximizeObjective(BaseObjective):
    pass


class CharacterizeObjective(BaseObjective):
    pass


class VirtualObjective(BaseObjective):
    observables: List[str]


OBJECTIVE_CLASSES = {
    "MINIMIZE": MinimizeObjective,
    "MAXIMIZE": MaximizeObjective,
    "CHARACTERIZE": CharacterizeObjective,
    "VIRTUAL": VirtualObjective
}


class VOCS(BaseModel):
    """
    Variables, Objectives, Constraints, and other Settings (VOCS) data structure
    to describe optimization problems.
    """

    variables: Dict[str, Union[ContinuousVariable, DiscreteVariable, FidelityVariable]]
    constraints: Dict[
        str, Union[LessThanConstraint, GreaterThanConstraint, BoundsConstraint]
    ] = Field(
        default={},
        description="constraint names with a list of constraint type and value",
    )
    objectives: Dict[
        str,
        Union[
            MinimizeObjective, MaximizeObjective, CharacterizeObjective, VirtualObjective]
    ] = Field(
        default={}, description="objective names with type of objective"
    )
    constants: Dict[str, Any] = Field(
        default={}, description="constant names and values passed to evaluate function"
    )
    observables: List[str] = Field(
        default=[],
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
                # if the length of the list is 2 we assume a continuous variable,
                # otherwise it's a discrete variable
                if len(val) == 2:
                    v[name] = ContinuousVariable(domain=val)
                else:
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
            if isinstance(val, BaseObjective):
                v[name] = val
            elif isinstance(val, dict):
                objective_type = val.pop("type")
                try:
                    class_ = globals()[objective_type]
                except KeyError:
                    raise ValueError(f"objective type {objective_type} is not "
                                     f"available")
                v[name] = class_(**val)
            elif isinstance(val, str):
                # Dynamically create the objective instance
                if val in ["MINIMIZE", "MAXIMIZE", "CHARACTERIZE"]:
                    v[name] = OBJECTIVE_CLASSES[val]()
                elif val == "VIRTUAL":
                    # TODO: handle virtual objectives
                    pass
                else:
                    raise ValueError(
                            f"Objective type '{val}' is not supported for '{name}'.")
            else:
                raise ValueError(f"objective input type {type(val)} not supported")

        return v