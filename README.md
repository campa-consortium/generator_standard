# Overview

This repository is an effort to standardize the interface of the **generators** in optimization libraries such as:

- [`Xopt`](https://github.com/ChristopherMayes/Xopt)
- [`optimas`](https://github.com/optimas-org/optimas)
- [`libEnsemble`](https://github.com/Libensemble/libensemble)
- [`rsopt`](https://github.com/radiasoft/rsopt)

**The objective of this effort is for these different libraries to be able to use each other's generators with little effort.**

*Example: [using `Xopt` generators in `optimas`](https://github.com/optimas-org/optimas/pull/151)*

# Definitions

- **Generator:**

  A generator is an object that recommends points to be evaluated in an optimization. It can also receive data (evaluations from past or ongoing optimization), which helps it make more informed recommendations.

  *Note:* The generator does **not** orchestrate the overall optimization (e.g. dispatch evaluations, etc.). As such, it is distinct from `libEnsemble`'s `gen_f` function, and is not itself "workflow" software.

  *Examples:
    - `Xopt`: [here](https://github.com/ChristopherMayes/Xopt/blob/main/xopt/generators/sequential/neldermead.py#L64) is the generator for the Nelder-Mead method. All Xopt generators implement the methods `generate` (i.e. make recommendations) and `add_data` (i.e. receive data).
    - `optimas`: [here](https://github.com/optimas-org/optimas/blob/main/optimas/generators/base.py#L27) is the base class for all generators. It implements the methods `suggest` (i.e. make recommendations) and `ingest` (i.e. receive data).

- **Variables, Objectives, Constraints (VOCS):**

  A `VOCS` is an object that specifies the names and types of components of the optimization problem that will be used by the generator. Each generator will validate that it can handle the specified set of variables, objectives, constraints, etc.


# Standardization

## VOCS
VOCs objects specify the following fields:

Inputs:
  - `variables`: defines the names and types of input parameters that will be passed to an objective function in order to solve the optimization problem.
  - `constants` (optional): defines the names and values of constant values that will be passed alongside `variables` to the objective function.

Outputs:
  - `objectives`: defines the names and types of function outputs that will be optimized or explored.
  - `constraints` (optional): defines the names and types of function outputs that will used as constraints that need to be satisfied for a valid solution to the optimization problem.
  - `observables` (optional): defines the names of any other function outputs that should be passed to the generator (alongside the `objectives` and `constraints`).

Example:

  ```python

  from generator_standard.vocs import VOCS

  >>> VOCS(
    variables = {"x1":[0, 1], "x2":[0, 5]},
    objectives = {"f1":"MAXIMIZE"},
    constants = {"alpha": 0.55},
    constraints = {"c1":["LESS_THAN", 0]},
    observables = {"o1"}
  )
  ```

**TODO:** See the docs for the complete API and more examples.

## Generators

Each generator will be a Python class that defines the following methods:

- **Constructor:**
  `__init__(self, vocs: VOCS, *args, **kwargs)`:

  The mandatory `VOCS` defines the input and output names used inside the generator.

  The constructor also accomodates variable positional and keyword arguments so each generator can be customized.

  Examples:

    ```python
    >>> generator = NelderMead(VOCS(variables={"x": [-5.0, 5.0], "y": [-3.0, 2.0]}, objectives={"f": "MAXIMIZE"}), adaptive=False)
    ```

- `_validate_vocs(self, vocs) -> None`:

  Validates the `VOCS` passed to the generator. Raises ``ValueError`` if the VOCS passed to the generator duing construction is invalid.

    Examples:

    ```python
    >>> generator = NelderMead(
      VOCS(variables={"x": [-5.0, 5.0], "y": [-3.0, 2.0]}, objectives={"f": "MAXIMIZE"}, constraints={"c":["LESS_THAN", 0.0]})
    )
    ValueError("NelderMead generator cannot accept constraints")
    ```

- `suggest(num_points: int | None = None) -> list[dict]`:

  Returns set of points in the input space, to be evaluated next. Each element of the list is a separate point.
  Keys of the dictionary include the name of each input variable specified in the constructor. Values of the dictionaries are **scalars**.

  When `num_points` is passed, the generator should return exactly this number of points, or raise a error ``ValueError`` if it is unable to.

  When `num_points` is not passed, the generator decides how many points to return.
  Different generators will return different number of points. For instance, the simplex would return 1 or 3 points. A genetic algorithm could return the whole population. Batched Bayesian optimization would return the batch size (i.e., number of points that can be processed in parallel), which would be specified in the constructor.

  In addition, some generators can generate a unique identifier for each generated point. If implemented, this identifier should appear in the dictionary under the key `"_id"`.
  When a generator produces an identifier, it must be included in the corresponding dictionary passed back to that generator in `ingest` (under the same key: `"_id"`).

  Examples:

    ```python

    >>> generator.suggest(2)
    [{"x": 1.2, "y": 0.8}, {"x": -0.2, "y": 0.4}]

    >>> generator.suggest(100)  # too many points
    ValueError

    >>> generator.suggest()
    [{"x": 1.2, "y": 0.8}, {"x": -0.2, "y": 0.4}, {"x": 4.3, "y": -0.1}]
    ```

- `ingest(points: list[dict])`:

  Feeds data (past evaluations) to the generator. Each element of the list is a separate point. Keys of the dictionary must include each named field specified in the `VOCS` provided
  to the generator on instantiation.

  Example:

  ```python
  >>> point = generator.suggest(1)
  >>> point
  [{"x": 1, "y": 1}]
  >>> point["f"] = objective(point)
  >>> point
  [{"x": 1, "y": 1, "f": 2}]
  >>> generator.ingest(point)
  ```

  Any points provided to the generator via `ingest` that were not created by the current generator instance should omit the `_id` field. If points are given to `ingest` with an `_id` value that is not known internally, a `ValueError` error should be raised.
  
- `finalize()`:

  **Optional**. Performs any work required to close down the generator. Some generators may need to close down background processes, files, databases,
  or dump data to disk. This is similar to calling `.close()` on an open file.

  Example:

  ```python
  >>> generator.finalize()
  ```
