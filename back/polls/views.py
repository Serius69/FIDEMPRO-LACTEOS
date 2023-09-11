from django.shortcuts import render
from django.http import HttpResponse
from scipy.stats import kstest
import random


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


def generate_random_numbers(request):
    N = 10

    actual = []
    for i in range(N):
        actual.append(random.random())

    x = kstest(actual, "norm")

    context = {
        'actual': actual,
        'ks_test_result': x,
    }