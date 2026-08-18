"""
Tests de finance.utils.analyze_simulation_results — guard de división por cero
cuando 'results' viene vacío (p.ej. una simulación cuyos días fallaron todos).
"""
from types import SimpleNamespace

from finance.utils import analyze_simulation_results


def _result(mean, std):
    return SimpleNamespace(demand_mean=mean, demand_std_deviation=std)


def test_analyze_simulation_results_averages():
    results = [_result(100, 10), _result(200, 20)]
    out = analyze_simulation_results(results)
    assert out['avg_demand_mean'] == 150
    assert out['avg_demand_std_dev'] == 15


def test_analyze_simulation_results_empty_does_not_raise():
    out = analyze_simulation_results([])
    assert out == {'avg_demand_mean': 0, 'avg_demand_std_dev': 0}
