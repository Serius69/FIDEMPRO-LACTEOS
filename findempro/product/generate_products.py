# generate_variables.py
from .products_data import products_data
from .models import Product

for data in products_data:
    Product.objects.create(**data)