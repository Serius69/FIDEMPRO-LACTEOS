from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from scipy.stats import kstest
import random
from .serializers import KSTestResultSerializer

class KSTestView(APIView):
    def get(self, request):
        N = 10
        actual = [random.random() for _ in range(N)]
        ks_test_result = kstest(actual, "norm")

        serializer = KSTestResultSerializer(data={
            'actual': actual,
            'ks_test_result': ks_test_result[0],
        })

        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
