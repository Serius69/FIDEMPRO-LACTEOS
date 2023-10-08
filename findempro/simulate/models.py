from django.db import models

class FDP(models.Model):
    name = models.CharField(max_length=100)
    lambda_param = models.FloatField()

    def __str__(self):
        return self.name

class DataPoint(models.Model):
    value = models.FloatField()

    def __str__(self):
        return f'DataPoint: {self.value}'

# Model to represent a Dairy SME
class DairySME(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

# Model to represent Financial Data for SMEs
class FinancialData(models.Model):
    sme = models.ForeignKey(DairySME, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    expenses = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.sme.name} - {self.year}"

# Model to represent Probability Density Functions (PDF)
class ProbabilityDensityFunction(models.Model):
    name = models.CharField(max_length=100)
    function_data = models.TextField()  # Store PDF function data (e.g., JSON, serialized data)

    def __str__(self):
        return self.name

# Model to represent Simulation Scenarios
class SimulationScenario(models.Model):
    pdfs = models.CharField(max_length=100)  # Adjust the field type and options as needed
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

# Model to link Simulation Scenarios with Probability Density Functions
class ScenarioPDF(models.Model):
    scenario = models.ForeignKey(SimulationScenario, on_delete=models.CASCADE)
    pdf = models.ForeignKey(ProbabilityDensityFunction, on_delete=models.CASCADE)
    weight = models.FloatField()  # Define the 'weight' field here if it's intended to be part of the model

    def __str__(self):
        return f"{self.scenario.name} - {self.pdf.name}"


# Model to represent Decision Support Analysis
class DecisionAnalysis(models.Model):
    sme = models.ForeignKey(DairySME, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    decision_description = models.TextField()
    recommendation = models.TextField()

    def __str__(self):
        return f"{self.sme.name} - {self.year} Analysis"
