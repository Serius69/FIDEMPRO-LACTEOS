
from django.shortcuts import render, get_object_or_404, redirect
from .form import UserForm
from product.models import Product
from business.models import Business
from variable.models import Variable
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin  # Create a Django form for Product
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User

# Create your views here.
# Profile
def profile_product_variable_list_view(request):
    products = Product.objects.all().order_by('-id')
    businesses = Business.objects.all().order_by('-id')
    variables = Variable.objects.all().order_by('-id')
    context = {'products': products, 'businesses': businesses, 'variables':variables}
    return render(request, 'user/profile.html', context)

# List
def user_list_view(request):
    users = User.objects.all().order_by('-id')
    context = {'users': users}
    return render(request, 'user/user-list.html', context)

# Create
def create_user_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()  # Save the form data to the database
            messages.success(request, 'User created successfully')
            return JsonResponse({'success': True})
        else:
            # Handle form validation errors
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = UserForm()
    return render(request, 'user/user-list.html', {'form': form})
# Update
def update_user_view(request,pk):
    user = User.objects.get(pk=pk)
    if request.method == "POST":
        form = UserForm(request.POST or None,request.FILES or None,instance=user)
        if form.is_valid():
            form.save()
            messages.success(request,"User updated successfully!")
            return redirect("user:user.overview")
        else:
            messages.error(request,"Something went wrong!")
            return redirect("product:product.overview")
    return render(request,"user/product-list.html")

# Delete
def delete_user_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Realiza la eliminación lógica (por ejemplo, establecer un campo "eliminado" en True)
    if request.method == 'POST':
        user.is_active = 0
        user.save()
        messages.success(request, "User deleted successfully!")
        return redirect("product:product.list")
    
    # Si se accede a la vista mediante GET, puedes mostrar un error o redirigir
    return HttpResponseForbidden("GET request not allowed for this view")
