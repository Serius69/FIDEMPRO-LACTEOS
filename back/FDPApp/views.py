from django.shortcuts import render
from scipy.stats import kstest
import random

def kstest_view(request):
    N = 10

    actual = []
    for i in range(N):
        actual.append(random.random())

    x = kstest(actual, "norm")

    context = {
        'actual': actual,
        'ks_test_result': x,
    }

    return render(request, 'myapp/kstest_template.html', context)
