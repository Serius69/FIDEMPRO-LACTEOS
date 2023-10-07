from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable
from .forms import VariableForm  # Create a Django form for Variable
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
# Create your variable views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# Companiesb 
# View for listing all variable
products_list = AppsView.as_view(template_name="variable/variable-list.html")
product_overview = AppsView.as_view(template_name="variable/variable-overview.html")
variables_stats = AppsView.as_view(template_name="variable/variable-stats.html")

# List
def variable_list(request,pk):
    variables = Variable.objects.all().order_by('-id')
    if variables:
        variable = Variable.objects.get(pk=pk)
    context = {'variable': variable}
    return render(request, 'variable/variable-list.html.html', context)

# Detail
def variable_view(request,pk):
    variable = Variable.objects.all().order_by('-id')
    if variable:
        company = Variable.objects.get(pk=pk)
    return render(request,"apps/crm/apps-crm-variable.html",{'variable':variable,'company':company})

# Create
def variable_view(request):
    variable = Variable.objects.all().order_by('-id')
    if request.method == "POST":
        form = VariableForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Company inserted successfully!")
            return redirect("apps:crm.variable")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.variable")
    return render(request,"apps/crm/apps-crm-variable.html",{'variable':variable})

# Update
def update_variable_view(request,pk):
    variable = Variable.objects.get(pk=pk)
    if request.method == "POST":
        form = VariableForm(request.POST or None,request.FILES or None,instance=variable)
        if form.is_valid():
            form.save()
            messages.success(request,"Company updated successfully!")
            return redirect("apps:crm.variable")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.variable")
    return render(request,"apps/crm/apps-crm-variable.html")

# Delete
def delete_variable_view(request,pk):
    variable = Variable.objects.get(pk=pk)
    variable.delete()
    messages.success(request,"Variable deleted successfully!")
    return redirect("apps:variable.list")
