from django.shortcuts import render, get_object_or_404, redirect
from simulate.models import ResultSimulation
from .models import FinancialDecision,FinanceRecommendation
from business.models import Business
from .forms import FinancialDecisionForm
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin  # Create a Django form for FinancialDecision
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.http import HttpResponseForbidden, HttpResponseServerError
# Create your views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
def make_decision(request):
    # Retrieve the simulation results from the database
    simulation_results = ResultSimulation.objects.all()
    
    # Analyze the results and make a financial decision
    decision = "Invest" if simulation_results[0].result_value > 500 else "Don't invest"

    return render(request, 'decision_template.html', {'decision': decision})
def finance_list_view(request):
    try:
        FinancialDecisions = FinancialDecision.objects.order_by('-id')
        businesses = Business.objects.order_by('-id')
        context = {'FinancialDecisions': FinancialDecisions, 'businesses': businesses}
        return render(request, 'FinancialDecision/FinancialDecision-list.html', context)
    except Exception as e:
        return HttpResponseServerError("Ocurrió un error al cargar la página. Por favor, inténtalo de nuevo más tarde.")
def create_finance_decision_view(request):
    if request.method == 'POST':
        form = FinancialDecisionForm(request.POST, request.FILES)
        if form.is_valid():
            FinancialDecision = form.save()
            messages.success(request, 'FinancialDecision created successfully')
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = FinancialDecisionForm()
    return render(request, 'finance/finance-list.html', {'form': form})
def update_finance_decision_view(request, pk):
    FinancialDecision = get_object_or_404(FinancialDecision, pk=pk)
    if request.method == "PUT":
        form = FinancialDecisionForm(request.PUT or None, request.FILES or None, instance=FinancialDecision)
        if form.is_valid():
            form.save()
            messages.success(request, "FinancialDecision updated successfully!")
        else:
            messages.error(request, "Something went wrong!")
        return redirect("FinancialDecision:FinancialDecision.overview")

    return render(request, "finance/financedecision-list.html")
def delete_finance_decision_view(request, pk):
    try:
        financialdecision = get_object_or_404(FinancialDecision, pk=pk)

        if request.method == 'PATCH':
            financialdecision.is_active = False
            financialdecision.save()
            messages.success(request, "FinancialDecision deleted successfully!")
            return redirect("finance:finance.list")

    except Exception as e:
        # Manejo de excepción. Puedes imprimir un mensaje de error o realizar otras acciones necesarias.
        error_message = str(e)
        messages.error(request, f"An error occurred: {error_message}")

    return HttpResponseForbidden("GET request not allowed for this view")
def get_finance_decision_details_view(request, pk):
    # Obtén los detalles del financialdecisiono en función del financialdecision_id
    if request.method == 'GET':
        financialdecision = FinanceRecommendation.objects.get(id=pk)

        financialdecision_details = {
            "name": financialdecision.name,
            "recommendation": financialdecision.recommendation,
            "description": financialdecision.description,
        }
    return JsonResponse(financialdecision_details)



 