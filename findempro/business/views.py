from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from .models import Business
from .forms import BusinessForm
from django.urls import reverse

# Create your business views here.

class AppsView(LoginRequiredMixin, TemplateView):
    pass

# List
def business_list(request):
    try:
        businesses = Business.objects.all().order_by('-id')
        context = {'businesses': businesses}  # Corrected the context variable name
        return render(request, 'business/business-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response

# Detail
def business_overview(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk)
        return redirect("business:business.overview", pk=business.pk)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response

# Create
def create_business_view(request):
    new_business = None  # Initialize new_business to None

    if request.method == "POST":
        # Create a form instance and populate it with data from the request
        form = BusinessForm(request.POST, request.FILES)

        try:
            # Check if the form data is valid
            if form.is_valid():
                # Create a new business object but don't save it to the database yet (commit=False)
                new_business = form.save(commit=False)
                # Set the user for the new business object
                new_business.user = request.user
                # Save the new business object to the database
                new_business.save()
                messages.success(request, "Business inserted successfully!")
                # Redirect to the business overview page, passing the new business's primary key (pk)
                return redirect("business:business.overview", pk=new_business.pk)
            else:
                messages.error(request, "Please check your inputs.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    else:
        # If it's not a POST request, create an empty form
        form = BusinessForm()

    # Render the business overview page, passing the new_business (which may be None)
    return render(request, "business/business-overview.html", {'business': new_business})

# Update
def update_business_view(request, pk):
    business = get_object_or_404(Business, pk=pk)
    if request.method == "POST":
        form = BusinessForm(request.POST, request.FILES, instance=business)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Business updated successfully!")
                return redirect("business:business_list")  # Corrected the redirect URL name
            else:
                messages.error(request, "Please check your inputs.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    form = BusinessForm(instance=business)  # Provide the form instance if it's a GET request
    return render(request, "business/business-update.html", {'form': form, 'business': business})

# Delete
def delete_business_view(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk)
        business.delete()
        messages.success(request, "Business deleted successfully!")
        return redirect("business:business_list")  # Corrected the redirect URL name
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response
