from abc import ABC, abstractmethod
from typing import Iterable, Optional, List

class Generator(ABC):
    """
    v 0.1

    Tentative ask/tell generator interface

    .. code-block:: python

        class MyGenerator(Generator):
            def __init__(self, my_parameter, my_keyword=None):
                self.model = init_model(my_parameter, my_keyword)

            def ask(self, num_points):
                return self.model.create_points(num_points)

            def tell(self, results):
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
    def ask(self, num_points: Optional[int]) -> List[dict]:
        """
        Request the next set of points to evaluate.

        .. code-block:: python

            >>> points = my_generator.ask(3)
            >>> print(points)
            [{"x": 1, "y": 1}, {"x": 2, "y": 2}, {"x": 3, "y": 3}]
        """

    def tell(self, results: List[dict]) -> None:
        """
        Send the results of evaluations to the generator.
        
        .. code-block:: python
        
            >>> results = [{"f": 1}, {"f": 4}, {"f": 9}]
            >>> my_generator.tell(results)
        """
