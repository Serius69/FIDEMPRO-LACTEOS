"""
Tests de formularios de la app finance.

Reescrito para el esquema vigente: el módulo anterior importaba
`FinanceRecommendationForm` (inexistente) y probaba `FinancialDecisionForm`
con campos de un modelo antiguo (type/location/image_src). Ahora prueba las
formas reales tras sanear `finance/forms.py`.
"""
import pytest
from finance.forms import FinancialDecisionForm, FinanceRecommendationForm


class TestFinancialDecisionForm:
    def test_missing_name_is_invalid(self):
        form = FinancialDecisionForm(data={'name': '', 'description': 'x'})
        assert not form.is_valid()
        assert 'name' in form.errors


class TestFinanceRecommendationForm:
    def test_valid_form(self):
        form = FinanceRecommendationForm(data={
            'name': 'Recomendación válida',
            'recommendation': 'Reducir inventario en un 15% este trimestre.',
            'description': 'Basado en la rotación observada.',
        })
        assert form.is_valid(), form.errors

    def test_empty_name_is_invalid(self):
        form = FinanceRecommendationForm(data={
            'name': '',
            'recommendation': 'Reducir inventario en un 15% este trimestre.',
        })
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_short_recommendation_is_invalid(self):
        form = FinanceRecommendationForm(data={
            'name': 'Recomendación',
            'recommendation': 'Corto',
        })
        assert not form.is_valid()
        assert 'recommendation' in form.errors
