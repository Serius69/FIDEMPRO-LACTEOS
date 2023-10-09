from django.shortcuts import render
import pkg_resources

from scipy import stats  # Import scipy for KS test
from .models import DataPoint, FDP, SimulationScenario
from .forms import *  # Replace with your actual form import
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class AppsView(LoginRequiredMixin, TemplateView):
    # Add methods or attributes specific to this view if needed
    template_name = 'your_template.html'  # Replace with your template name

def ks_test_view(request):
    # Retrieve the dataset and FDP parameters
    data_points = DataPoint.objects.values_list('value', flat=True)
    fdp = FDP.objects.get(pk=1)  # You need to specify the FDP you want to test against

    # Calculate the KS statistic and p-value
    ks_statistic, p_value = stats.kstest(data_points, 'expon', args=(0, 1/fdp.lambda_param))

    # Interpret the results (you can customize this part)
    if p_value < 0.05:
        result = "Reject null hypothesis: Data does not fit the FDP."
    else:
        result = "Fail to reject null hypothesis: Data fits the FDP."

    context = {
        'ks_statistic': ks_statistic,
        'p_value': p_value,
        'result': result,
    }

    return render(request, 'ks_test_result.html', context)

def simulate_init(request):
    businesses = SimulationScenario.objects.all().order_by('-id')
    business = businesses.first()  # Retrieve the first object if it exists

    context = {'simulate': business}
    return render(request, 'simulate/simulate-init.html', context)
