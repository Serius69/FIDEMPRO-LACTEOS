from rest_framework import serializers
from .models import FDP, DataPoint
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'simulatename', 'password')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        simulate = User.objects.create_simulate(**validated_data)
        Token.objects.create(simulate=simulate)
        return simulate

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = FDP
        fields = ('id', 'title', 'description', 'no_of_ratings', 'avg_rating')

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPoint
        fields = ('id', 'stars', 'simulate', 'movie')