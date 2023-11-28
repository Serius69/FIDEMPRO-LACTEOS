# utils.py
from .models import ResultSimulation

def get_results_for_simulation(simulation_id):
    return ResultSimulation.objects.filter(fk_simulation_id=simulation_id)

