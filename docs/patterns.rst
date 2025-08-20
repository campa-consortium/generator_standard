.. _patterns:

=====================
Common Usage Patterns
=====================

Within Jupyter notebook or interpreter
--------------------------------------

.. code-block:: python

    from my_objective import my_objective_function
    from generator_standard.tests.test_generator import RandomGenerator
    from generator_standard.vocs import VOCS

    vocs = VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": "MINIMIZE"})
    gen = RandomGenerator(vocs)

    points = gen.suggest(10)
    for point in points:
        point["f"] = my_objective_function(point["x"])

    gen.ingest(points)

Within workflow library - libEnsemble
-------------------------------------

`libEnsemble <https://github.com/Libensemble/libensemble>`_ is a Python
workflow toolkit for coordinating asynchronous and dsynamic ensembles
of calculations. It plans to support plugging in standard generators similarly
to the following:

.. code-block:: python

    from generator_standard.tests.test_generator import RandomGenerator
    from generator_standard.vocs import VOCS

    from my_objective import libE_styled_objective_function

    from libensemble import Ensemble
    from libensemble.specs import GenSpecs, ExitCriteria

    vocs = VOCS(variables={"x": [0.0, 1.0]}, objectives={"f": "MINIMIZE"})
    gen = RandomGenerator(vocs)

    workflow = Ensemble()

    workflow.sim_specs = SimSpecs(
        sim_f = libE_styled_objective_function,
        inputs = ["x"]
        outputs = [("f", float)],
    )

    workflow.gen_specs = GenSpecs(
        generator=gen,
        persis_in=["f"],  # keep passing "f" results to the standard generator
        outputs=[("x", float)],
        initial_batch_size=10,
        batch_size=5
    )

    workflow.exit_criteria = ExitCriteria(sim_max=500)

    results = workflow.run()
