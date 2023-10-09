from django.db import models

class FDP(models.Model):
    name = models.CharField(max_length=100)
    lambda_param = models.FloatField()

    def __str__(self):
        return self.name

class NormalFDP(FDP):
    mean = models.FloatField()
    std_deviation = models.FloatField()

    def __str__(self):
        return f"Normal - {self.name}"

class ExponentialFDP(FDP):
    def __str__(self):
        return f"Exponential - {self.name}"

class LogarithmicFDP(FDP):
    def __str__(self):
        return f"Logarithmic - {self.name}"

class DataPoint(models.Model):
    value = models.FloatField()

    def __str__(self):
        return f'DataPoint: {self.value}'

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
    pdfs = models.ManyToManyField(ProbabilityDensityFunction)  # Use ManyToManyField to link with PDFs
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class ScenarioPDF(models.Model):
    scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    pdf = models.ForeignKey(ProbabilityDensityFunction, on_delete=models.CASCADE)
    weight = models.FloatField()  # Define the 'weight' field here if it's intended to be part of the model

    def __str__(self):
        return f"{self.scenario.name} - {self.pdf.name}"

class DecisionAnalysis(models.Model):
    sme = models.ForeignKey(DairySME, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    decision_description = models.TextField()
    recommendation = models.TextField()

    def __str__(self):
        return f"{self.sme.name} - {self.year} Analysis"
