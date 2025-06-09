import pytest
import random
from generator_standard.generator import Generator
from generator_standard.vocs import VOCS, ContinuousVariable


class RandomGenerator(Generator):
    def __init__(self, vocs: VOCS):
        super().__init__(vocs)
        self.vocs = vocs
        self.data = []
        self.best_point = None
        random.seed(0)

    def _validate_vocs(self, vocs: VOCS) -> None:
        """This generator should have atleast one variable and one objective"""
        if not vocs.variables:
            raise ValueError("VOCS must define at least one variable.")
        if not vocs.objectives:
            raise ValueError("VOCS must define at least one objective.")
        for var in vocs.variables.values():
            if not hasattr(var, "domain"):
                raise ValueError("RandomGenerator only supports continuous variables")

    def suggest(self, num_points: int | None = None) -> list[dict]:
        """Suggest points from the generator"""
        if num_points is None:
            num_points = 1
        max_pts = self.vocs.constants.get("max_points")
        if max_pts is not None and num_points > max_pts:
            raise ValueError(f"Cannot supply more than {max_pts} points")

        suggestions = []
        for _ in range(num_points):
            point = {
                k: random.uniform(*v.domain)
                for k, v in self.vocs.variables.items()
            }
            suggestions.append(point)
        return suggestions

    def ingest(self, results: list[dict]) -> None:
        """Ingest results into the generator"""
        # Only add point if it satisfies all constraints
        for r in results:
            violated = False
            for name, constraint in self.vocs.constraints.items():
                val = r.get(name)
                if not constraint.check(val):
                    violated = True
            if not violated:
                self.data.append(r)

        # Set the best point
        direction = self.vocs.objectives["f"]
        for r in self.data:
            val = r.get("f")
            if self.best_point is None:
                self.best_point = r
            elif direction == "MINIMIZE" and val < self.best_point["f"]:
                self.best_point = r
            elif direction == "MAXIMIZE" and val > self.best_point["f"]:
                self.best_point = r

    def finalize(self) -> None:
        pass


def test_gen_fails_without_variable():
    with pytest.raises(ValueError, match="at least one variable"):
        RandomGenerator(VOCS(
            variables={},
            objectives={"f": "MINIMIZE"},
        ))

def test_gen_fails_without_objective():
    with pytest.raises(ValueError, match="at least one objective"):
        RandomGenerator(VOCS(
            variables={"x": [0, 1]},
            objectives={},
        ))


def test_gen_fails_with_discrete_variable():
    vocs = VOCS(
        variables={"x": {"a", "b", "c"}},
        objectives={"f": "MINIMIZE"},
    )
    with pytest.raises(ValueError, match="only supports continuous variables"):
        RandomGenerator(vocs)


def test_suggest_max_points():
    vocs_local = VOCS(
        variables={"x": [0.0, 1.0]},
        objectives={"f": "MINIMIZE"},
        constants={"max_points": 3},
    )
    gen = RandomGenerator(vocs_local)
    gen.suggest(3)
    with pytest.raises(ValueError, match="Cannot supply more than 3 points"):
        gen.suggest(5)


def test_best_point_selection():
    pts = [{"x": 0.1, "f": 1.8}, {"x": 0.2, "f": 1.5}, {"x": 0.3, "f": 2.0}]
    vocs = VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": "MINIMIZE"})
    gen = RandomGenerator(vocs)
    gen.ingest(pts)
    assert gen.best_point == {"x": 0.2, "f": 1.5}, "Incorrect best point"

    vocs1 = VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": "MAXIMIZE"})
    gen1 = RandomGenerator(vocs1)
    gen1.ingest(pts)
    assert gen1.best_point == {"x": 0.3, "f": 2.0}, "Incorrect best point"


# Define VOCS with a BOUNDS constraint
vocs_full = VOCS(
    variables={
        "x": [0.0, 10.0],  # simple specification
        "y": ContinuousVariable(domain=[-5.0, 5.0])  # Provide as object
    },
    objectives={"f": "MINIMIZE"},
    constraints={
        "c": ["GREATER_THAN", 5.5],
        "c1": ["BOUNDS", -5.0, 5.0],
        "c2": ["LESS_THAN", -4.0]
    },
    constants={"alpha": 1.0},
    observables=["temp"]
)


def test_gen_has_constant_alpha():
    gen = RandomGenerator(vocs_full)
    assert "alpha" in gen.vocs.constants


def test_suggest_default_single_point():
    gen = RandomGenerator(vocs_full)
    pts = gen.suggest()
    assert isinstance(pts, list)
    assert len(pts) == 1


def test_gen_with_constraints():
    # Create generator
    gen = RandomGenerator(vocs_full)

    # Suggest points
    pts = gen.suggest(5)
    print("Suggested input points:")
    for pt in pts:
        print(pt)

    # Simulate evaluation and add results
    for pt in pts:
        pt["f"] = pt["x"] ** 2 + pt["y"] ** 2  # dummy objective
        pt["temp"] = pt["x"] - pt["y"]         # dummy observable
        pt["c"] = pt["x"] - pt["y"]            # dummy constraint
        pt["c1"] = pt["x"] + pt["y"]           # dummy constraint
        pt["c2"] = pt["y"] * 2                 # dummy constraint

    print('')

    # Ingest results
    gen.ingest(pts)

    print('\nResults:')
    for pt in gen.data:
        print(pt)

    assert len(gen.data) == 1, f"Expected 1 point in gen.data but found {len(gen.data)}"
    expected = {'x': 4.21, 'y': -2.41, 'f': 23.50, 'temp': 6.62, 'c': 6.62, 'c1': 1.79, 'c2': -4.82}
    actual = {k: round(gen.data[0][k], 2) for k in expected}
    assert actual == expected
    assert list(gen.vocs.objectives.values())[0] == "MINIMIZE"
    gen.finalize()
