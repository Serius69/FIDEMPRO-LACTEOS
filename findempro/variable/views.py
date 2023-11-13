from django.shortcuts import render, get_object_or_404, redirect
from .models import Variable
from product.models import Product
from .forms import VariableForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
import openai
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
openai.api_key = settings.OPENAI_API_KEY
class AppsView(LoginRequiredMixin, TemplateView):
    pass
def variable_list(request):
    try:
        variables = Variable.objects.all().order_by('-id')
        products = Product.objects.all().order_by('-id')

        # Paginate the variables
        paginator = Paginator(variables, 10)  # Show 10 variables per page
        page = request.GET.get('page')

        try:
            variables = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            variables = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            variables = paginator.page(paginator.num_pages)

        context = {'variables': variables, 'products': products}
        return render(request, 'variable/variable-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
def variable_overview(request, pk):
    try:
        variable = get_object_or_404(Variable, pk=pk)
        return render(request, "variable/variable-overview.html", {'variable': variable})
    except Exception as e:
        messages.error(request, "An error occurred. Please check the server logs for more information.")
        return HttpResponse(status=500)
def create_variable_view(request):
    if request.method == 'POST':
        form = VariableForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                variable_name = form.cleaned_data.get('name')
                initial_prompt = f"Generate the initials of the variable, but only use 4 characters. Do not include additional advertisements or instructions. Provide the initials for the next variable: {variable_name}"

                response = openai.Completion.create(
                    engine="text-davinci-002",
                    prompt=initial_prompt,
                    max_tokens=5,
                    stop=None
                )
                initials = response.choices[0].text.strip()

                form.instance.initials = initials

                variable = form.save()
                messages.success(request, 'Variable created successfully')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'error': 'An error occurred while saving the variable'})
    else:
        form = VariableForm()
    return render(request, 'variable/variable-form.html', {'form': form})
def update_variable_view(request, pk):
    variable = Variable.objects.get(pk=pk)
    if request.method == "POST":
        form = VariableForm(request.POST or None, request.FILES or None, instance=variable)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Variable updated successfully!")
                return redirect("variable:variable.overview", pk=pk)
            else:
                messages.error(request, "Something went wrong!")
                return render(request, "variable/variable-form.html", {'form': form})
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return HttpResponse(status=500)

    return render(request, "variable/variable-form.html", {'form': form})
def delete_variable_view(request, pk):
    try:
        variable = get_object_or_404(Variable, pk=pk)
        variable.delete()
        messages.success(request, "Variable deleted successfully!")
        return redirect("variable:variable.list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)