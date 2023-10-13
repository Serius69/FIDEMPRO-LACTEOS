from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable
from product.models import Product
from .forms import VariableForm  # Create a Django form for Variable
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
import openai
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone

openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# List
def variable_list(request):
    variables = Variable.objects.all().order_by('-id')
    products = Product.objects.all().order_by('-id')
    context = {'variable': variables, 'products': products}
    return render(request, 'variable/variable-list.html', context)

# Detail
def variable_overview(request,pk):
    variables = Variable.objects.all().order_by('-id')
    if variables:
        variable = Variable.objects.get(pk=pk)
    return render(request,"variable/variable-overview.html",{'variable':variable,'variable':variable})
# Create
def create_variable_view(request):
    if request.method == 'POST':
        form = VariableForm(request.POST, request.FILES)

        if form.is_valid():
            # Retrieve the variable name from the form's cleaned data
            variable_name = form.cleaned_data.get('name')
            initial_prompt = f"Generate the initials of the variable, but only use 4 characters. Do not include additional advertisements or instructions. Provide the initials for the next variable: {variable_name}"

            # Call the OpenAI API to generate initials
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=initial_prompt,
                max_tokens=5,  # Adjust the token limit as needed
                stop=None  # You can set stop words if needed
            )
            initials = response.choices[0].text.strip()

            # Set 'initials' in the form instance
            form.instance.initials = initials

            try:
                variable = form.save()  # Save the form data to the database
                messages.success(request, 'Variable created successfully')
                return JsonResponse({'success': True})
            except Exception as e:
                # Handle any unexpected errors (e.g., database save errors)
                print(e)  # Log the error for debugging
                return JsonResponse({'success': False, 'error': 'An error occurred while saving the variable'})
        else:
            # Return form validation errors if the form is not valid
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = VariableForm()
    return render(request, 'variable/variable-list.html', {'form': form})

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

