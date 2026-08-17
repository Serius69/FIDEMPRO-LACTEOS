import pytest
from django.contrib.auth.models import User

from business.models import Business
from pages.views.simulation_creator import (
    create_and_save_questionary_result,
    create_enhanced_simulation,
    get_answer_data_for_product,
    get_simulation_data_for_product,
)
from product.models import Product
from questionary.models import Answer, Questionary, QuestionaryResult


@pytest.mark.django_db
def test_legacy_onboarding_does_not_persist_fixture_answers():
    user = User.objects.create_user(username='truth-audit', password='unused')
    business = Business.objects.create(
        name='Truth Audit Business', type=1, location='La Paz', fk_user=user,
    )
    product = Product.objects.create(
        name='Audit Product', description='Test product', fk_business=business,
    )
    questionary = Questionary.objects.create(
        questionary='Incomplete questionnaire', fk_product=product,
    )

    assert create_and_save_questionary_result(questionary) is True

    result = QuestionaryResult.objects.get(fk_questionary=questionary)
    assert Answer.objects.filter(fk_questionary_result=result).count() == 0


def test_runtime_fixture_lookup_is_explicitly_disabled():
    assert get_answer_data_for_product('leche') == []
    assert get_simulation_data_for_product('leche') == []


def test_legacy_enhanced_simulation_requires_explicit_user_data():
    with pytest.raises(ValueError, match='LEGACY_SYNTHETIC_SIMULATION_DISABLED'):
        create_enhanced_simulation(None)
