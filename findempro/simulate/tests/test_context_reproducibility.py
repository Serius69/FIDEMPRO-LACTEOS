from types import SimpleNamespace

import numpy as np

from simulate.services.context_manager import SimulationContextManager
from simulate.utils.simulation_core_utils import SimulationCore


def test_context_projection_noise_uses_simulation_seed():
    simulation = SimpleNamespace(random_seed=17)
    first_manager = SimulationContextManager()
    second_manager = SimulationContextManager()

    first_manager._setup_services(simulation)
    second_manager._setup_services(simulation)
    first = first_manager._generate_smooth_projection([], [10, 12, 11, 13, 12])
    second = second_manager._generate_smooth_projection([], [10, 12, 11, 13, 12])

    assert first == second


def test_legacy_random_equation_uses_the_core_rng():
    first_core = SimulationCore()
    second_core = SimulationCore()
    first_core._rng = np.random.default_rng(23)
    second_core._rng = np.random.default_rng(23)

    assert first_core._preprocess_expression("random()") == second_core._preprocess_expression("random()")
