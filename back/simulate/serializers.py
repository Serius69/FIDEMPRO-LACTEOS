from rest_framework import serializers
from .models import FDP, DataPoint
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class SimulateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FDP
        fields = ('id', 'title', 'description', 'no_of_ratings', 'avg_rating')
