import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from business.models import Business
from modeling.models import BusinessModelDefinition
from modeling.schema import empty_model_spec
from modeling.services import create_model_version
from modeling.statistics import DistributionFitError, fit_distributions

pytestmark = pytest.mark.django_db


def test_distribution_lab_returns_reviewable_candidates_and_diagnostics():
    result = fit_distributions([1, 2, 2, 3, 4, 5], candidates=["normal", "poisson", "lognormal"])

    assert result["requires_review"] is True
    assert result["provenance"] == "USER_ENTERED_OBSERVATIONS"
    assert result["quantiles"]["p50"] == 2.5
    assert {candidate["distribution"] for candidate in result["candidates"]} == {"normal", "poisson", "lognormal"}
    assert all("aic" in candidate and "bic" in candidate for candidate in result["candidates"])
    assert all(candidate["p_value"] is None for candidate in result["candidates"])
    assert result["ranking"] == {
        "criterion": "AIC_THEN_DIAGNOSTIC_WITHIN_LIKELIHOOD_FAMILY",
        "comparable": False,
        "selected_distribution": None,
        "unavailable_reason": "MIXED_LIKELIHOOD_FAMILIES",
    }


def test_distribution_lab_rejects_non_finite_and_unknown_candidates():
    with pytest.raises(DistributionFitError, match="finita"):
        fit_distributions([1, 2, 3, 4, float("nan")])
    with pytest.raises(DistributionFitError, match="no soportadas"):
        fit_distributions([1, 2, 3, 4, 5], candidates=["made_up"])


def test_continuous_fit_exposes_real_statistic_but_not_naive_fitted_ks_pvalue():
    sample = [-2.1, -1.3, -0.8, -0.2, 0.0, 0.3, 0.7, 1.2, 1.9]

    result = fit_distributions(sample, candidates=["normal"])
    diagnostic = result["candidates"][0]

    assert diagnostic["test_name"] == "kolmogorov_smirnov_distance"
    assert 0 <= diagnostic["statistic"] <= 1
    assert diagnostic["p_value"] is None
    assert diagnostic["p_value_unavailable_reason"] == "PARAMETERS_ESTIMATED_FROM_SAME_SAMPLE"
    assert result["ranking"]["selected_distribution"] == "normal"


def test_exponential_fit_is_real_and_reproducible():
    sample = [0.2, 0.5, 0.8, 1.1, 1.7, 2.4, 3.2, 4.8]

    first = fit_distributions(sample, candidates=["exponential"])
    second = fit_distributions(sample, candidates=["exponential"])

    assert first == second
    assert first["candidates"][0]["parameters"]["rate"] > 0


def test_count_fit_uses_discrete_diagnostic_not_continuous_ks():
    result = fit_distributions(
        [0, 1, 1, 2, 2, 2, 3, 4, 1, 2],
        data_semantics="count",
    )
    diagnostic = result["candidates"][0]

    assert diagnostic["distribution"] == "poisson"
    assert diagnostic["test_name"] == "discrete_cdf_max_distance"
    assert diagnostic["ks_statistic"] is None
    assert diagnostic["p_value"] is None
    assert diagnostic["p_value_unavailable_reason"] == "DISCRETE_TEST_NOT_CALIBRATED"


def test_distribution_fit_rejects_small_constant_and_bad_domain_samples():
    with pytest.raises(DistributionFitError, match="entre 5"):
        fit_distributions([1, 2, 3, 4])
    with pytest.raises(DistributionFitError, match="compatible"):
        fit_distributions([5, 5, 5, 5, 5])

    result = fit_distributions([-2, -1, 0, 1, 2], candidates=["normal", "lognormal"])
    assert [item["distribution"] for item in result["rejected"]] == ["lognormal"]
    assert result["ranking"]["selected_distribution"] == "normal"


def test_distribution_fit_api_is_owner_scoped_and_does_not_publish_model_data():
    owner = get_user_model().objects.create_user(username="fit-owner", password="password")
    other = get_user_model().objects.create_user(username="fit-other", password="password")
    business = Business.objects.create(name="Fit business", location="La Paz", fk_user=owner)
    definition = BusinessModelDefinition.objects.create(business=business, name="Fit model", created_by=owner)
    create_model_version(definition, empty_model_spec(name="Fit model"), user=owner)
    client = Client()
    client.force_login(owner)

    response = client.post(
        reverse("modeling:model-distribution-fit", kwargs={"model_id": definition.id}),
        data={"observations": [2, 3, 4, 5, 6], "candidates": ["normal"]},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["requires_review"] is True
    assert response.json()["candidates"][0]["p_value"] is None
    assert response.json()["candidates"][0]["method_version"] == "distribution_fit_v2"
    assert definition.current_version.data_imports.count() == 0

    client.force_login(other)
    assert client.post(
        reverse("modeling:model-distribution-fit", kwargs={"model_id": definition.id}),
        data={"observations": [2, 3, 4, 5, 6]},
        content_type="application/json",
    ).status_code == 404
