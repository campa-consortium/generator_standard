from abc import ABC, abstractmethod
from .vocs import VOCS


class Generator(ABC):
    """
    Tentative suggest/ingest generator interface

    .. code-block:: python

        class MyGenerator(Generator):
            def __init__(self, my_parameter, my_keyword=None):
                self.model = init_model(my_parameter, my_keyword)

            def suggest(self, num_points):
                return self.model.create_points(num_points)

            def ingest(self, results):
                self.model.update_model(results)


        my_generator = MyGenerator(my_parameter=100)
    """

    @abstractmethod
    def __init__(self, vocs: VOCS, *args, **kwargs):
        """
        Initialize the Generator object on the user-side. Constants, class-attributes,
        and preparation goes here.

        .. code-block:: python

            >>> my_generator = MyGenerator(vocs, my_keyword=10)
        """
        self._validate_vocs(vocs)

    @abstractmethod
    def _validate_vocs(self, vocs) -> None:
        """
        Validate if the vocs object is compatible with the current generator. Should
        raise a ValueError if the vocs object is not compatible with the generator
        object
        """

    @abstractmethod
    def suggest(self, num_points: int | None) -> list[dict]:
        """
        Request the next set of points to evaluate.

        .. code-block:: python

            >>> points = my_generator.suggest(3)
            >>> print(points)
            [{"x": 1, "y": 1}, {"x": 2, "y": 2}, {"x": 3, "y": 3}]
        """

    def ingest(self, results: list[dict]) -> None:
        """
        Send the results of evaluations to the generator.

        .. code-block:: python

            >>> results = [{"x": 0.5, "y": 1.5, "f": 1}, {"x": 2, "y": 3, "f": 4}]
            >>> my_generator.ingest(results)
        """

    def finalize(self) -> None:
        """
        Perform any work required to close down the generator.

        .. code-block:: python

            >>> my_generator.finalize()
        """
