import importlib.util
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[3] / "scripts" / "load" / "findempro_load_harness.py"
SPEC = importlib.util.spec_from_file_location("findempro_load_harness", HARNESS)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_harness_defaults_prepare_only_and_small():
    args = MODULE.parser().parse_args([])
    assert args.organizations == 1
    assert args.concurrency == 1
    assert args.smoke is False
    assert args.free_ratio == 3
    assert args.dataset_size == 100


@pytest.mark.parametrize("option", ["--organizations", "--concurrency", "--dataset-size", "--duration"])
def test_harness_rejects_non_positive_dimensions(option):
    with pytest.raises(SystemExit):
        MODULE.parser().parse_args([option, "0"])


@pytest.mark.parametrize(
    ("label", "expected"),
    [("SMALL_DATASET", 100), ("MEDIUM_DATASET", 1000), ("LARGE_ALLOWED_DATASET", 10_000)],
)
def test_harness_accepts_named_safe_dataset_profiles(label, expected):
    assert MODULE.parser().parse_args(["--dataset-size", label]).dataset_size == expected


def test_free_ratio_means_free_organizations_per_paid_organization():
    args = MODULE.parser().parse_args(["--organizations", "25", "--free-ratio", "3"])
    assert MODULE.preflight(args)["total_organizations"] == 100
