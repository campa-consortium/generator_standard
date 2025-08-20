from abc import ABC, abstractmethod
from .vocs import VOCS


class Generator(ABC):
    """
    Each standardized generator is a Python class that inherits from this class.

    .. code-block:: python

        class MyGenerator(Generator):
            def __init__(self, VOCS, my_parameter, my_keyword=None):
                self.model = init_model(VOCS, my_parameter, my_keyword)

            def suggest(self, num_points):
                return self.model.create_points(num_points)

            def ingest(self, results):
                self.model.update_model(results)

            def finalize(self):
                self.model.dump()

        my_generator = MyGenerator(my_parameter=100)
        results = simulate(my_generator.suggest(10))
        my_generator.ingest(results)
        my_generator.finalize()

    """

    @abstractmethod
    def __init__(self, vocs: VOCS, *args, **kwargs):
        """
        The mandatory :ref:`VOCS<vocs>` defines the input and output names used inside the generator.

        The constructor also accomodates variable positional and keyword arguments so each generator can be customized.

        .. code-block:: python

            >>> my_generator = MyGenerator(vocs, my_parameter, my_keyword=10)

        .. code-block:: python

            >>> generator = NelderMead(VOCS(variables={"x": [-5.0, 5.0], "y": [-3.0, 2.0]}, objectives={"f": "MAXIMIZE"}), adaptive=False)
        """
        self._validate_vocs(vocs)

    @abstractmethod
    def _validate_vocs(self, vocs) -> None:
        """
        Validate if the ``VOCS`` is compatible with the current generator. Should
        raise a ``ValueError`` if it is incompatible.

        .. code-block:: python

            >>> generator = NelderMead(
                    VOCS(
                        variables={"x": [-5.0, 5.0], "y": [-3.0, 2.0]},
                        objectives={"f": "MAXIMIZE"},
                        constraints={"c":["LESS_THAN", 0.0]}
                    )
                )

            ValueError("NelderMead generator cannot accept constraints")
        """

    @abstractmethod
    def suggest(self, num_points: int | None) -> list[dict]:
        """
        Returns set of points in the input space, to be evaluated next.
        Each element of the list is a separate point. Keys of the dictionary include the name
        of each input variable specified in the constructor. Values of the dictionaries are **scalars**.

        When ``num_points`` is passed, the generator should return exactly this number of points, or raise
        a error ``ValueError`` if it is unable to.

        When ``num_points`` is not passed, the generator decides how many points to return.
        Different generators will return different number of points. For instance, the simplex
        would return 1 or 3 points. A genetic algorithm could return the whole population.
        Batched Bayesian optimization would return the batch size (i.e., number of points that
        can be processed in parallel), which would be specified in the constructor.

        In addition, some generators can generate a unique identifier for each generated point.
        If implemented, this identifier should appear in the dictionary under the key ``"_id"``.
        When a generator produces an identifier, it must be included in the corresponding
        dictionary passed back to that generator in ``ingest`` (under the same key: ``"_id"``).

        .. code-block:: python

            >>> points = my_generator.suggest(3)
            >>> print(points)
            [{"x": 1, "y": 1}, {"x": 2, "y": 2}, {"x": 3, "y": 3}]

            >>> generator.suggest(100)  # too many points
            ValueError

            >>> generator.suggest()
            [{"x": 1.2, "y": 0.8}, {"x": -0.2, "y": 0.4}, {"x": 4.3, "y": -0.1}]
        """

    def ingest(self, results: list[dict]) -> None:
        """
        Feeds data (past evaluations) to the generator. Each element of the list is a separate point.
        Keys of the dictionary must include each named field specified in the ``VOCS`` provided
        to the generator on instantiation.

        Any points provided to the generator via ``ingest`` that were not created by the current generator
        instance should omit the ``_id`` field. If points are given to ``ingest`` with an ``_id`` value that is
        not known internally, a ``ValueError`` error should be raised.

        .. code-block:: python

            >>> results = [{"x": 0.5, "y": 1.5, "f": 1}, {"x": 2, "y": 3, "f": 4}]
            >>> my_generator.ingest(results)
            ...
            >>> point = generator.suggest(1)
            >>> point
            [{"x": 1, "y": 1}]
            >>> point["f"] = objective(point)
            >>> point
            [{"x": 1, "y": 1, "f": 2}]
            >>> generator.ingest(point)
        """

    def finalize(self) -> None:
        """
        **Optional**. Performs any work required to close down the generator. Some generators may need
        to close down background processes, files, databases, or dump data to disk. This is similar to calling
        ``.close()`` on an open file.

        .. code-block:: python

            >>> my_generator.finalize()
        """
