from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Business
from .forms import *
from django.contrib import messages

# Create your business views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# Companies
# View for listing all business
apps_business_list = AppsView.as_view(template_name="apps/business/business-list.html")
apps_business_overview = AppsView.as_view(template_name="apps/business/business-overview.html")

# List
def business_list(request,pk):
    businesses = Business.objects.all().order_by('-id')
    if businesses:
        business = Business.objects.get(pk=pk)
    context = {'business': business}
    return render(request, 'business/business-list.html.html', context)

# Detail
def business_view(request,pk):
    business = Business.objects.all().order_by('-id')
    if business:
        company = Business.objects.get(pk=pk)
    return render(request,"apps/crm/apps-crm-business.html",{'business':business,'company':company})

# Create
def business_view(request):
    business = Business.objects.all().order_by('-id')
    if request.method == "POST":
        form = BusinessForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Company inserted successfully!")
            return redirect("apps:crm.business")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.business")
    return render(request,"apps/crm/apps-crm-business.html",{'business':business})

# Update
def update_business_view(request,pk):
    business = Business.objects.get(pk=pk)
    if request.method == "POST":
        form = BusinessForm(request.POST or None,request.FILES or None,instance=business)
        if form.is_valid():
            form.save()
            messages.success(request,"Company updated successfully!")
            return redirect("apps:crm.business")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.business")
    return render(request,"apps/crm/apps-crm-business.html")

# Delete
def delete_business_view(request,pk):
    business = Business.objects.get(pk=pk)
    business.delete()
    messages.success(request,"Business deleted successfully!")
    return redirect("apps:business.list")
