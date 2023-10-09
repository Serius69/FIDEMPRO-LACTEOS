from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable
from product.models import Product
from .forms import VariableForm  # Create a Django form for Variable
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
import openai
# 
openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# List
def variable_list(request):
    variables = Variable.objects.all().order_by('-id')
    # if variables:
    #     variable = Variable.objects.get(pk=pk)
    context = {'variable': variables}
    return render(request, 'variable/variable-list.html', context)

# Detail
def variable_overview(request,pk):
    variables = Variable.objects.all().order_by('-id')
    if variables:
        variable = Variable.objects.get(pk=pk)
    
    return render(request,"variable/variable-overview.html",{'variable':variable,'variable':variable})

# Create
def create_variable_view(request):
    products = Product.objects.all().order_by('-id')
    variable = Variable.objects.all().order_by('-id')
    context = {'variable': variable, 'product': products}
    if request.method == "POST":
        form = VariableForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Variable inserted successfully!")
            return redirect("variable:variable.overview")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("variable:variable.overview")
    return render(request,"variable/variable-list.html",context)

# Update
def update_variable_view(request,pk):
    variable = Variable.objects.get(pk=pk)
    if request.method == "POST":
        form = VariableForm(request.POST or None,request.FILES or None,instance=variable)
        if form.is_valid():
            form.save()
            messages.success(request,"Variable updated successfully!")
            return redirect("variable:variable.overview")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("variable:variable.overview")
    return render(request,"variable/variable-list.html")

# Delete
def delete_variable_view(request,pk):
    variable = Variable.objects.get(pk=pk)
    variable.delete()
    messages.success(request,"Variable deleted successfully!")
    return redirect("variable:variable.list")

