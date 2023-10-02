from django.db import models

class FDP(models.Model):
    name = models.CharField(max_length=100)
    lambda_param = models.FloatField()

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'simulate'

class DataPoint(models.Model):
    value = models.FloatField()

    def __str__(self):
        return f'DataPoint: {self.value}'

    class Meta:
        app_label = 'simulate'

class DairySME(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class FinancialData(models.Model):
    sme = models.ForeignKey(DairySME, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    expenses = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.sme.name} - {self.year}"

class ProbabilityDensityFunction(models.Model):
    name = models.CharField(max_length=100)
    function_data = models.TextField()  # Store PDF function data (e.g., JSON, serialized data)

    def __str__(self):
        return self.name

class SimulationScenario(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    pdfs = models.ManyToManyField(ProbabilityDensityFunction, through='ScenarioPDF')

    def __str__(self):
        return self.name

class ScenarioPDF(models.Model):
    scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    pdf = models.ForeignKey(ProbabilityDensityFunction, on_delete=models.CASCADE)
    weight = models.FloatField()  # Add a weight for the PDF's contribution to the scenario

    def __str__(self):
        return f"{self.scenario.name} - {self.pdf.name}"

class DecisionAnalysis(models.Model):
    sme = models.ForeignKey(DairySME, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    decision_description = models.TextField()
    recommendation = models.TextField()

    def __str__(self):
        return f"{self.sme.name} - {self.year} Analysis"
