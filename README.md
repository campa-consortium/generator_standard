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
    - `optimas`: [here](https://github.com/optimas-org/optimas/blob/main/optimas/generators/base.py#L27) is the base class for all generators. It implements the methods `ask` (i.e. make recommendations) and `tell` (i.e. receive data).

# Standardization

Each type of generator (e.g., Nelder-Nead, different flavors of GA, BO, etc.) will be a Python class that defines the following methods:

- `__init__(*args, **kwargs)`:

  The constructor will include variable positional and keyword arguments to
  accommodate the different options that each type of generator has.

- `ask(num_points: Optional[int] = None) -> List[Dict]`:

  Returns a set of points in the input space to be evaluated next. Each element of the list is a separate point.
  Keys of the dictionary correspond to the name of each input variable.

  - Points are represented as dictionaries. Each dictionary can contain whichever keys are relevant to that generator, but each dictionary in a set should have the same keys:

  ```python
  >>> generator.ask(2)
  [{"x": 3, "y": 4}, {"x": 1, "y": 2}]
  ```

  - When `num_points` is not passed, the generator decides how many points to return.
    Different generators will return different number of points, by default. For instance, the simplex would return 1 or 3 points. A genetic algorithm could return the whole population. Batched Bayesian optimization would return the batch size (i.e., number of points that can be processed in parallel), which would be specified in the constructor.

  - When it is passed: the generator should return exactly this number of points, or raise ``ValueError`` if it is unable to. If the user is flexible about the number of points, it should simply not pass `num_points`.

  ```python
  >>> generator.ask(100)  # too many points
  ValueError
  ```

  ```python
  >>> generator.ask()
  [{"x": 1, "y": 1}, {"x": 2, "y": 2}, {"x": 3, "y": 3}]
  ```

- `tell(points: List[Dict])`:

  Feeds data (past/complete evaluations) to the generator.

  - Evaluation dictionaries must resemble dictionaries from `ask()`, with some update:

  ```python
  >>> point = generator.ask(1)
  >>> point
  [{"x": 1, "y": 1}]
  >>> point["f"] = objective(point)
  >>> point
  [{"x": 1, "y": 1, "f": 2}]
  >>> generator.tell(point)

- **OPTIONAL**: `ask_updates() -> List[Dict]`

  Returns a set of previously returned points that presumably contain some adjustments. For optimization algorithms, these may be points that have been identified as minima.
  Other algorithms may want to cancel or disregard previous points.

  - Any generator implementing this method must include ``"id"`` as a key to distinguish each point, with corresponding values being unique:

  ```python
  >>> point = generator.ask(1)
  >>> point
  [{"x": 1, "y": 1, "id": 1, "is_minima": False}]
  >>> point["f"] = objective(point)
  >>> point
  [{"x": 1, "y": 1, "f": 2, "id": 1, "is_minima": False}]
  >>> generator.tell(point)
  >>> generator.ask_updates()
  [{"x": 1, "y": 1, "f": 2, "id": 1, "is_minima": True}]
  ```

  - If no updates are available, return an empty list.
