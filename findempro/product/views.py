from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import ProductForm
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin  # Create a Django form for Product
# Create your product views here.
class AppsView(LoginRequiredMixin,TemplateView):
    pass
# List
def product_list(request):
    products = Product.objects.all().order_by('-id')
    # if productes:
    #     product = Product.objects.get(pk=pk)
    context = {'product': products}
    return render(request, 'product/product-list.html', context)

# Detail
def product_overview(request,pk):
    product = Product.objects.all().order_by('-id')
    if product:
        product = Product.objects.get(pk=pk)
    return render(request,"product/product-overview.html",{'product':product,'product':product})

# Create
def create_product_view(request):
    product = Product.objects.all().order_by('-id')
    if request.method == "POST":
        form = ProductForm(request.POST or None,request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request,"Company inserted successfully!")
            return redirect("apps:crm.product")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.product")
    return render(request,"product/product-list.html",{'product':product})

# Update
def update_product_view(request,pk):
    product = Product.objects.get(pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST or None,request.FILES or None,instance=product)
        if form.is_valid():
            form.save()
            messages.success(request,"Company updated successfully!")
            return redirect("apps:crm.product")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("apps:crm.product")
    return render(request,"product/product-list.html")

# Delete
def delete_product_view(request,pk):
    product = Product.objects.get(pk=pk)
    product.delete()
    messages.success(request,"Product deleted successfully!")
    return redirect("apps:product.list")

