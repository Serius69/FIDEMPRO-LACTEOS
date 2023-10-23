import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse
from .models import Business
from .forms import BusinessForm
from django.urls import reverse
from django.http import JsonResponse

# Create your business views here.
class AppsView(LoginRequiredMixin, TemplateView):
    pass

# List
def business_list(request):
    form = BusinessForm()
    try:
        businesses = Business.objects.filter(user=request.user).order_by('-id')
        context = {'businesses': businesses, 'form': form}  # Corrected the context variable name
        return render(request, 'business/business-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response

# Detail
def business_overview(request, pk):
    # Configure logging within the function or view.
    logger = logging.getLogger(__name__)
    logger.debug("This is a log message.")
    try:
        business = get_object_or_404(Business, pk=pk)
        return render(request, 'business/business-overview.html', {'business': business})
    except Exception as e:
        # Log the complete error.
        logger.exception("An error occurred in the 'business_overview' view")
        messages.error(request, "An error occurred. Please check the server logs for more information: ", e)
        return HttpResponse(status=500)  # Return an HTTP 500 error response

@login_required
def create_business_view(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                business = form.save()  # Save the form data to the database
                messages.success(request, 'Business created successfully')
                return JsonResponse({'success': True})
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return JsonResponse({'success': False, 'error': f"An error occurred: {str(e)}"})
        else:
            # Handle form validation errors
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = BusinessForm()
    return render(request, 'business/business-form.html', {'form': form})

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
