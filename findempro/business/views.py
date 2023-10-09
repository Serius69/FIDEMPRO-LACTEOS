from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Business
from business.forms import BusinessForm
from django.contrib import messages

# Create your business views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# List
def business_list(request):
    businesses = Business.objects.all().order_by('-id')
    # if businesses:
    #     business = Business.objects.get(pk=pk)
    context = {'business': businesses}
    return render(request, 'business/business-list.html', context)

# Detail
def business_overview(request,pk):
    business = Business.objects.all().order_by('-id')
    if business:
        business = Business.objects.get(pk=pk)
    return render(request,"business/business-overview.html",{'business':business,'business':business})

def create_business_view(request):
    if request.method == "POST":
        form = BusinessForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Business inserted successfully!")
            return redirect("business:business.list")
        else:
            messages.error(request, "Something went wrong! Please check your inputs.")
    else:
        form = BusinessForm()

    return render(request, "business/business-list.html", {'form': form})


# Update
def update_business_view(request,pk):
    business = Business.objects.get(pk=pk)
    if request.method == "POST":
        form = BusinessForm(request.POST or None,request.FILES or None,instance=business)
        if form.is_valid():
            form.save()
            messages.success(request,"Business updated successfully!")
            return redirect("business:crm.business")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("business:crm.business")
    return render(request,"business/business-list.html")

# Delete
def delete_business_view(request,pk):
    business = Business.objects.get(pk=pk)
    business.delete()
    messages.success(request,"Business deleted successfully!")
    return redirect("business:business.list")
