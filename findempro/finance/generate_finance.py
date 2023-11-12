# generate_variables.py
from .finance_data import finance_data
from .models import FinanceRecommendation

for data in finance_data:
    FinanceRecommendation.objects.create(**data)
