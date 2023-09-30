from rest_framework import serializers

class KSTestResultSerializer(serializers.Serializer):
    actual = serializers.ListField(child=serializers.FloatField())
    ks_test_result = serializers.FloatField()
