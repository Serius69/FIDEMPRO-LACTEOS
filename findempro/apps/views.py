from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CrmContact,CrmCompany,CrmLead,JobApplication,EcommerceOrder,EcommerceCustomer,TicketList
from .forms import *
from django.contrib import messages

# Create your views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# Companies
apps_companies_list = AppsView.as_view(template_name="apps/company/company-list.html")
apps_companies_overview = AppsView.as_view(template_name="apps/company/company-overview.html")
# Products
apps_products_list = AppsView.as_view(template_name="apps/product/products-list.html")
apps_product_overview = AppsView.as_view(template_name="apps/product/products-overview.html")
# Variables
apps_variables_list = AppsView.as_view(template_name="apps/variable/variable-list.html")
apps_variables_overview= AppsView.as_view(template_name="apps/variable/variable-overview.html")
apps_variables_stats = AppsView.as_view(template_name="apps/variable/variable-stats.html")
#Users pages
apps_users_list = AppsView.as_view(template_name="apps/user/users-list.html")
apps_users_overview = AppsView.as_view(template_name="apps/user/users-overview.html")
# CRM
apps_crm_deals_view = AppsView.as_view(template_name="apps/crm/apps-crm-deals.html")
# Simulate
apps_simulate_init = AppsView.as_view(template_name="apps/simulate/simulate-init.html")
# Reports
apps_reports_list = AppsView.as_view(template_name="apps/reports/reports-list.html")
apps_reports_overview = AppsView.as_view(template_name="apps/reports/reports-overview.html")

# Crm Contact views
def apps_crm_contacts_view(request,pk):
    contacts = CrmContact.objects.all().order_by('-id')
    if contacts:
        contact = CrmContact.objects.get(pk=pk)
    return render(request,"apps/crm/apps-crm-contacts.html",{'contacts':contacts,'contact':contact})

def apps_crm_add_contacts_view(request):
    contacts = CrmContact.objects.all().order_by("-id")
    
    if request.method == 'POST':
        form = CrmContactAddForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Contact inserted successfully!")
            return redirect("apps:crm.contacts")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.contacts")
    return render(request,"apps/crm/apps-crm-contacts.html",{'contacts':contacts})

def apps_crm_update_contacts_view(request,pk):
    contact = CrmContact.objects.get(pk=pk)
    if request.method == "POST":
        form = CrmContactUpdateForm(request.POST or None,request.FILES or None,instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request,"Contact updated successfully!")
            return redirect("apps:crm.contacts")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.contacts")
    return render(request,'apps/crm/apps-crm-contacts.html',{'contact':contact})

def apps_crm_delete_contacts_view(request,pk):
    contacts = CrmContact.objects.get(pk=pk)
    contacts.delete()
    messages.success(request,"Contact deleted successfully!")
    return redirect("apps:crm.contacts")

# Crm Companies views

def apps_crm_companies_view(request,pk):
    companies = CrmCompany.objects.all().order_by('-id')
    if companies:
        company = CrmCompany.objects.get(pk=pk)
    return render(request,"apps/crm/apps-crm-companies.html",{'companies':companies,'company':company})

def apps_crm_add_companies_view(request):
    companies = CrmCompany.objects.all().order_by('-id')
    if request.method == "POST":
        form = CrmCompanyAddForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Company inserted successfully!")
            return redirect("apps:crm.companies")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.companies")
    return render(request,"apps/crm/apps-crm-companies.html",{'companies':companies})

def apps_crm_update_companies_view(request,pk):
    companies = CrmCompany.objects.get(pk=pk)
    if request.method == "POST":
        form = CrmCompanyUpdateForm(request.POST or None,request.FILES or None,instance=companies)
        if form.is_valid():
            form.save()
            messages.success(request,"Company updated successfully!")
            return redirect("apps:crm.companies")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.companies")
    return render(request,"apps/crm/apps-crm-companies.html")

def apps_crm_delete_companies_view(request,pk):
    companies = CrmCompany.objects.get(pk=pk)
    companies.delete()
    messages.success(request,"Contact deleted successfully!")
    return redirect("apps:crm.companies")

# Crm Leads views

def apps_crm_leads_view(request):
    leads = CrmLead.objects.all().order_by('-id')
    if request.method == 'POST':
        form = CrmLeadsAddForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Lead inserted successfully!")
            return redirect("apps:crm.leads")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.leads")
    return render(request,"apps/crm/apps-crm-leads.html",{'leads':leads})

def apps_crm_update_leads_view(request,pk):
    lead = CrmLead.objects.get(pk=pk)
    if request.method == "POST":
        form = CrmLeadsUpdateForm(request.POST or None,request.FILES or None,instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request,"Lead Updated successfully!")
            return redirect("apps:crm.leads")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.leads")
    return render(request,"apps/crm/apps-crm-leads.html")

def apps_crm_delete_leads_view(request,pk):
    leads = CrmLead.objects.get(pk=pk)
    leads.delete()
    messages.success(request,"Contact deleted successfully!")
    return redirect("apps:crm.leads")

def apps_users_application_view(request):
    apps = JobApplication.objects.all().order_by('-id')
    if request.method == "POST":
        form = JobApplicationForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Application inserted Successfully!")
            return redirect("apps:users.application")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:users.application")
    return render(request,'apps/userss/apps-users-application.html',{'apps':apps})

def apps_users_update_application_view(request,pk):
    apps = JobApplication.objects.get(pk=pk)
    if request.method == "POST":
        form = JobApplicationForm(request.POST or None, request.FILES or None, instance=apps)
        if form.is_valid():
            form.save()
            messages.success(request,"Application updated Successfully!")
            return redirect("apps:users.application")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:users.application")
    return render(request,'apps/userss/apps-users-application.html')

def apps_users_delete_application_view(request,pk):
    apps = JobApplication.objects.get(pk=pk)
    apps.delete()
    messages.success(request,"Application deleted Successfully!")
    return redirect("apps:users.application")

def apps_companies_orders_view(request):
    orders = EcommerceOrder.objects.all().order_by('-id')
    if request.method == "POST":
        form = EcommerceOrderForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Order inserted Successfully!")
            return redirect("apps:companies.orders")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:companies.orders")
    return render(request,'apps/companies/apps-companies-orders.html',{'orders':orders})

def apps_companies_update_orders_view(request,pk):
    orders = EcommerceOrder.objects.get(pk=pk)
    if request.method == 'POST':
        form = EcommerceOrderForm(request.POST or None, request.FILES or None,instance=orders)
        if form.is_valid():
            form.save()
            messages.success(request,"Order updated Successfully!")
            return redirect("apps:companies.orders")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:companies.orders")
    return render(request,'apps/companies/apps-companies-orders.html')

def apps_companies_delete_orders_view(request,pk):
    orders = EcommerceOrder.objects.get(pk=pk)
    orders.delete()
    messages.success(request,"Order deleted Successfully!")
    return redirect("apps:companies.orders")

def apps_companies_customers_view(request):
    customers = EcommerceCustomer.objects.all().order_by('-id')
    if request.method == "POST":
        form = EcommerceCustomerForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Customer inserted Successfully!")
            return redirect("apps:companies.customers")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:companies.customers")
    return render(request,'apps/companies/apps-companies-customers.html',{'customers':customers})

def apps_companies_update_customers_view(request,pk):
    customers = EcommerceCustomer.objects.get(pk=pk)
    if request.method == 'POST':
        form = EcommerceCustomerForm(request.POST or None, request.FILES or None,instance=customers)
        if form.is_valid():
            form.save()
            messages.success(request,"Customer updated Successfully!")
            return redirect("apps:companies.customers")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:companies.customers")
    return render(request,'apps/companies/apps-companies-customers.html')

def apps_companies_delete_customers_view(request,pk):
    customers = EcommerceCustomer.objects.get(pk=pk)
    customers.delete()
    messages.success(request,"Customer deleted Successfully!")
    return redirect("apps:companies.customers")

def apps_tickets_list_view(request):
    tickets = TicketList.objects.all().order_by('-id')
    if request.method == "POST":
        form = TicketListForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Tickets inserted Successfully!")
            return redirect("apps:tickets.list")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:tickets.list")
    return render(request,'apps/support-tickets/apps-tickets-list.html',{'tickets':tickets})

def apps_tickets_update_list_view(request,pk):
    tickets = TicketList.objects.get(pk=pk)
    if request.method == "POST":
        form = TicketListForm(request.POST or None,request.FILES or None,instance=tickets)
        if form.is_valid():
            form.save()
            messages.success(request,"Tickets inserted Successfully!")
            return redirect("apps:tickets.list")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:tickets.list")
    return render(request,'apps/support-tickets/apps-tickets-list.html')

def apps_tickets_delete_list_view(request,pk):
    tickets = TicketList.objects.get(pk=pk)
    tickets.delete()
    messages.success(request,"Tickets deleted Successfully!")
    return redirect("apps:tickets.list")
