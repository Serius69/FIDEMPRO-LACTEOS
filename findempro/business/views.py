from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Business
from business.forms import BusinessForm
from django.contrib import messages
from django.http import HttpResponse
# Create your business views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# List
def business_list(request):
    try:
        businesses = Business.objects.all().order_by('-id')
        context = {'business': businesses}
        return render(request, 'business/business-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response

# Detail
def business_overview(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk)
        return render(request, "business/business-overview.html", {'business': business})
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response

def create_business_view(request):
    if request.method == "POST":
        form = BusinessForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Business inserted successfully!")
                return redirect("business:business.list")
            else:
                messages.error(request, "Please check your inputs.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    else:
        form = BusinessForm()

    return render(request, "business/business-list.html", {'form': form})

# Update
def update_business_view(request, pk):
    business = get_object_or_404(Business, pk=pk)
    if request.method == "POST":
        form = BusinessForm(request.POST or None, request.FILES or None, instance=business)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "Business updated successfully!")
                return redirect("business:business.list")
            else:
                messages.error(request, "Please check your inputs.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    return render(request, "business/business-list.html")

# Delete
def delete_business_view(request, pk):
    try:
        business = get_object_or_404(Business, pk=pk)
        business.delete()
        messages.success(request, "Business deleted successfully!")
        return redirect("business:business.list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)  # Return an HTTP 500 error response
