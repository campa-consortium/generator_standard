# Overview

This repository is an effort to standardize the interface of the **generators** in optimization libraries such as [`Xopt`](https://github.com/ChristopherMayes/Xopt), [`optimas`](https://github.com/optimas-org/optimas), [`libEnsemble`](https://github.com/Libensemble/libensemble), [`rsopt`](https://github.com/radiasoft/rsopt).

**The objective of this effort is for these different libraries to be able to use each other's generators with little effort.**

*Example: [using `Xopt` generators in `optimas`](https://github.com/optimas-org/optimas/pull/151)*

# Definitions

- **Generator:**

  A generator is an object that recommends points to be evaluated in an optimization. It can also receive data (evaluations from past or on-going optimization), which helps it make more informed recommendations.

  *Note:* The generator does **not** orchestrate the overall optimization (e.g. dispatch evaluations, etc.). As such, it is distinct from `libEnsemble`'s `gen_f` function, and is not itself "workflow" software.

  *Examples:
    - `Xopt`: [here](https://github.com/ChristopherMayes/Xopt/blob/main/xopt/generators/scipy/neldermead.py#L64) is the generator for the Nelder-Mead method. All Xopt generators implement the methods `generate` (i.e. make recommendations) and `add_data` (i.e. receive data).
    - `optimas`: [here](https://github.com/optimas-org/optimas/blob/main/optimas/generators/base.py#L27) is the base class for all generators. It implements the methods `suggest` (i.e. make recommendations) and `ingest` (i.e. receive data).

- **Variables, Objectives, Constraints (VOCs):**

  A VOCS is an object that specifies the name and types of components of the optimization problem that will be used by the generator. Each generator will validate that it can handle the specified set of variables, objectives, constraints, etc.


# Standardization

## VOCs
VOCs objects specify the following fields:
  - `variables`: defines the names and types of input parameters that will be passed to an objective function need to be chosen in order to solve the optimization problem
  - `objectives`: defines the names and types of function outputs that will be optimized or characterized
  - `constraints`: defines the names and types of function outputs that will used as constraints that need to be satisfied for a valid solution to the optimization problem.
  - `constants`: defines the names and values of constant values that will be passed alongside `variables` to the objective function
  - `observables`: defines the names of values that will be tracked by the generator alongside the `objectives` and `constraints`

## Generators

Each type of generator (e.g., Nelder-Nead, different flavors of GA, BO, etc.) will be a Python class that defines the following methods:

- **Constructor:**
  `__init__(self, vocs: VOCS, *args, **kwargs)`:

  The contructor has one mandatory argument:

  - `VOCS` object that defines the input and output names used inside the generator

  The constructor will also include variable positional and keyword arguments to
  accommodate the different options that each type of generator has.

  Examples:

    ```python
    >>> generator = NelderMead(VOCS(variables={"x": [-5.0, 5.0], "y": [-3.0, 2.0]}, objectives={"f": "MAXIMIZE"}))
    ```

- `_validate_vocs(self, vocs) -> None`:

  Validates the vocs passed to the generator. Raises ``ValueError`` if the generator cannot use the VOCs passed to the generator duing construction.

- `suggest(num_points: int | None = None) -> list[dict]`:

  Returns set of points in the input space, to be evaluated next. Each element of the list is a separate point.
  Keys of the dictionary include the name of each input variable specified in the constructor. Values of the dictionaries are **scalars**.

  In addition, some generators can generate a unique identification number for each point that they generate. In that case, this identification number appears in the dictionary under the key `"_id"`.
  When a generator produces an identification number, it is important that the identification number is included in the corresponding dictionary passed to this generator in `ingest` (under the same key: `"_id"`).

  - When `num_points` is not passed: the generator decides how many points to return.
    Different generators will return different number of points, by default. For instance, the simplex would return 1 or 3 points. A genetic algorithm could return the whole population. Batched Bayesian optimization would return the batch size (i.e., number of points that can be processed in parallel), which would be specified in the constructor.

  - When it is passed: the generator should return exactly this number of points, or raise a error ``ValueError`` if it is unable to. If the user is flexible about the number of points, it should simply not pass `num_points`.

  Examples:

    ```python
    >>> generator.suggest(100)  # too many points
    ValueError
    ```

    ```python
    >>> generator.suggest()
    [{"x": 1.2, "y": 0.8}, {"x": -0.2, "y": 0.4}, {"x": 4.3, "y": -0.1}]
    ```

- `ingest(points: list[dict])`:

  Feeds data (past evaluations) to the generator. Each element of the list is a separate point. Keys of the dictionary must include to the name of each variable and objective specified in the contructor.

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

- `finalize()`:

  **Optional**. Performs any work required to close down the generator. Many generators may need to close down background processes, open files, databases,
  or dump data to disk. This is similar to calling `.close()` on an open file.

  Example:

  ```python
  >>> generator.finalize()
  ```