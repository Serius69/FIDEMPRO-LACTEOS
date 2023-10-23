from django.shortcuts import render
from simulate.models import DemandSimulation
# Create your views here.

def make_decision(request):
    # Retrieve the simulation results from the database
    simulation_results = DemandSimulation.objects.all()
    
    # Analyze the results and make a financial decision
    decision = "Invest" if simulation_results[0].result_value > 500 else "Don't invest"

    return render(request, 'decision_template.html', {'decision': decision})