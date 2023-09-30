from rest_framework import serializers
from .models import Variable
from django.contrib.auth.models import User

class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variable
        fields = ('id', 'name', 'price', 'stock')
