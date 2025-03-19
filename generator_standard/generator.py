from abc import ABC, abstractmethod

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
    def __init__(self, *args, **kwargs):
        """
        Initialize the Generator object on the user-side. Constants, class-attributes,
        and preparation goes here.

        .. code-block:: python

            >>> my_generator = MyGenerator(my_parameter, my_keyword=10)
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
