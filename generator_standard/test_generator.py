from generator_standard.generator import Generator
from generator_standard.vocs import VOCS, ContinuousVariable
import random

class RandomGenerator(Generator):
    def __init__(self, vocs: VOCS):
        super().__init__(vocs)
        self.vocs = vocs
        self.data = []

    def _validate_vocs(self, vocs: VOCS) -> None:
        # This generator only supports ContinuousVariable inputs
        for var in vocs.variables.values():
            if not hasattr(var, "domain"):
                raise ValueError("RandomGenerator only supports variables with domain (e.g. ContinuousVariable)")

    def suggest(self, num_points: int | None = None) -> list[dict]:
        if num_points is None:
            num_points = 1
        suggestions = []
        for _ in range(num_points):
            point = {
                k: random.uniform(*v.domain)
                for k, v in self.vocs.variables.items()
            }
            suggestions.append(point)
        return suggestions

    def ingest(self, results: list[dict]) -> None:
        # SH - A check all method - could it go in generator base class?
        for r in results:
            violated = False
            for name, constraint in self.vocs.constraints.items():
                val = r.get(name)
                # print(f'{name} val: {val}')
                if val is None:
                    continue
                if not constraint.check(val):
                    violated = True

                    #SH tmp check - messages too specific
                    if hasattr(constraint, "value"):
                        print(f"{name} violated: {val} > {constraint.value} - discarding")
                    else:
                        lo, hi = constraint.range
                        print(f"{name} violated: {val} not in [{lo}, {hi}] - discarding")
                    break

            if not violated:
                self.data.append(r)


    def finalize(self) -> None:
        # Nothing to clean up in this simple example
        pass


# Define VOCS with a BOUNDS constraint
vocs = VOCS(
    variables={
        "x": ContinuousVariable(domain=[0.0, 10.0]),
        "y": ContinuousVariable(domain=[-5.0, 5.0])
    },
    objectives={"f": "MINIMIZE"},
    constraints={
        "c": ["GREATER_THAN", 0.5],
        "c1": ["BOUNDS", -2.0, 2.0]
    },
    constants={"alpha": 1.0},
    observables=["temp"]
)

# Create generator
gen = RandomGenerator(vocs)

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

print('')

# Ingest results
gen.ingest(pts)

print('\nResults:')
for pt in gen.data:
    print(pt)