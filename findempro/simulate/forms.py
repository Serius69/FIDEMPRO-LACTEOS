from django import forms
from .models import DairySME, FinancialData, ProbabilityDensityFunction, SimulationScenario, ScenarioPDF, DecisionAnalysis

class DairySMEForm(forms.ModelForm):
    class Meta:
        model = DairySME
        fields = ('name', 'location', 'description')

class FinancialDataForm(forms.ModelForm):
    class Meta:
        model = FinancialData
        fields = ('sme', 'year', 'revenue', 'expenses', 'profit')

class ProbabilityDensityFunctionForm(forms.ModelForm):
    class Meta:
        model = ProbabilityDensityFunction
        fields = ('name', 'function_data')

class SimulationScenarioForm(forms.ModelForm):
    class Meta:
        model = SimulationScenario
        fields = ('name', 'description', 'pdfs')

class ScenarioPDFForm(forms.ModelForm):
    class Meta:
        model = ScenarioPDF
        fields = ('scenario', 'pdf', 'weight')

class DecisionAnalysisForm(forms.ModelForm):
    class Meta:
        model = DecisionAnalysis
        fields = ('sme', 'year', 'decision_description', 'recommendation')
