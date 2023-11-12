# generate_variables.py
from .variables_data import variables_data
from .models import Variable

for data in variables_data:
    Variable.objects.create(**data)
