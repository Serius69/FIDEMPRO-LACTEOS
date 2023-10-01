from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable
from .forms import VariableForm  # Create a Django form for Variable

def variable_list(request):
    variables = Variable.objects.all()
    return render(request, 'variable_list.html', {'variables': variables})

def variable_detail(request, id):
    variable = get_object_or_404(Variable, id=id)
    return render(request, 'variable_detail.html', {'variable': variable})

def add_variable(request):
    if request.method == 'POST':
        form = VariableForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('variable_list')
    else:
        form = VariableForm()
    return render(request, 'add_variable.html', {'form': form})

def edit_variable(request, id):
    variable = get_object_or_404(Variable, id=id)
    if request.method == 'POST':
        form = VariableForm(request.POST, instance=variable)
        if form.is_valid():
            form.save()
            return redirect('variable_list')
    else:
        form = VariableForm(instance=variable)
    return render(request, 'edit_variable.html', {'form': form, 'variable': variable})

def delete_variable(request, id):
    variable = get_object_or_404(Variable, id=id)
    if request.method == 'POST':
        variable.delete()
        return redirect('variable_list')
    return render(request, 'delete_variable.html', {'variable': variable})
