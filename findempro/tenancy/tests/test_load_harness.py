import importlib.util
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[3] / "scripts" / "load" / "findempro_load_harness.py"
SPEC = importlib.util.spec_from_file_location("findempro_load_harness", HARNESS)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_harness_defaults_prepare_only_and_small():
    args = MODULE.parser().parse_args([])
    assert args.organizations == 1
    assert args.concurrency == 1
    assert args.smoke is False


@pytest.mark.parametrize("option", ["--organizations", "--concurrency", "--dataset-size", "--duration"])
def test_harness_rejects_non_positive_dimensions(option):
    with pytest.raises(SystemExit):
        MODULE.parser().parse_args([option, "0"])
