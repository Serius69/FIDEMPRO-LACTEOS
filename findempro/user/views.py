from django.shortcuts import render, get_object_or_404, redirect
from .forms import UserForm
from user.models import UserProfile
from product.models import Product
from business.models import Business
from variable.models import Variable
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import login
from findempro.forms import UserLoginForm
@login_required
def pages_profile_settings(request):
    user = request.user
    profile = UserProfile.objects.get(user=user)
    if profile.is_profile_complete():
        completeness_percentage = 100
    else:
        total_fields = len([field for field in profile._meta.get_fields() if field.name != 'id' and field.name != 'user'])
        completed_fields = len([field for field in profile._meta.get_fields() if field.name != 'id' and field.name != 'user' and getattr(profile, field.name)])

        completeness_percentage = (completed_fields / total_fields) * 100
    context = {'completeness_percentage': completeness_percentage, 
               'user': user, 
               'profile': profile,
               'selected_state': profile.state,  # Add this line
                'selected_country': profile.country,  # Add this line
               }
    return render(request, 'user/profile-settings.html', context)
@login_required
def profile_product_variable_list_view(request):
    user = request.user
    products = Product.objects.filter(fk_business__fk_user=user, is_active=True).order_by('-id')
    businesses = Business.objects.filter(fk_user=user, is_active=True).order_by('-id')
    variables = Variable.objects.filter(fk_product__fk_business__fk_user=user, is_active=True).order_by('-id')
    
    profile = UserProfile.objects.get(user=user)
    paginator_variables = Paginator(variables, 10)  # Show 10 variables per page
    paginator_products = Paginator(products, 10)  # Show 10 products per page
    page = request.GET.get('page')
    
    business_count = businesses.count()
    product_count = products.count()
    variable_count = variables.count()

    completeness_percentage = calculate_completeness_percentage(profile)
        
    variables, products = paginate_variables_and_products(page, paginator_variables, paginator_products)
        
    context = {
        'products': products, 
        'businesses': businesses, 
        'variables': variables , 
        'completeness_percentage': completeness_percentage,
        'business_count': business_count,
        'product_count': product_count,
        'variable_count': variable_count
    }
    return render(request, 'user/profile.html', context)

def calculate_completeness_percentage(profile):
    if profile.is_profile_complete():
        return 100
    else:
        total_fields = len([field for field in profile._meta.get_fields() if field.name != 'id' and field.name != 'user'])
        completed_fields = len([field for field in profile._meta.get_fields() if field.name != 'id' and field.name != 'user' and getattr(profile, field.name)])
        return (completed_fields / total_fields) * 100

def paginate_variables_and_products(page, paginator_variables, paginator_products):
    try:
        variables = paginator_variables.page(page)
        products = paginator_products.page(page)
    except PageNotAnInteger:
        variables = paginator_variables.page(1)
        products = paginator_products.page(1)
    except EmptyPage:
        variables = paginator_variables.page(paginator_variables.num_pages)
        products = paginator_products.page(paginator_products.num_pages)
    return variables, products
@login_required
def user_list_view(request):
    try:
        users = User.objects.all().order_by('-id')
        context = {'users': users}
        return render(request, 'user/user-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
@login_required
def create_user_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                form.save()  # Save the form data to the database
                messages.success(request, 'User created successfully')
                return JsonResponse({'success': True})
            else:
                # Handle form validation errors
                return JsonResponse({'success': False, 'errors': form.errors})
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return JsonResponse({'success': False, 'error': 'An error occurred while saving the user'})
    else:
        form = UserForm()
    return render(request, 'user/user-list.html', {'form': form})
@login_required
def update_user_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == "POST":
        form = UserForm(request.POST or None, request.FILES or None, instance=user)
        try:
            if form.is_valid():
                form.save()
                messages.success(request, "User updated successfully!")
                return redirect("user:user.overview")
            else:
                messages.error(request, "Please check your inputs.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    form = UserForm(instance=user)  # Provide the form instance if it's a GET request
    return render(request, "user/user-update.html", {'form': form, 'user': user})
@login_required
def delete_user_view_as_admin(request, pk):
    user = get_object_or_404(User, pk=pk)
    try:
        user.is_active = False
        user.save()
        messages.success(request, "User deleted successfully!")
        return redirect("user:user.list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
@login_required
def  change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important for maintaining the user's session
            messages.success(request, 'Your password was successfully changed.')
            return redirect('profile')  # Redirect to the user's profile or another appropriate page
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'user/profile.html', {'form': form})    
@login_required
def delete_user_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    try:
        user.is_active = False
        user.save()
        messages.success(request, "User deleted successfully!")
        return redirect("signup_url")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)
@login_required
def deactivate_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            request.user.is_active = False
            request.user.save()
            messages.success(request, 'Your account has been deactivated.')
            return redirect('login')  # Cambia 'login' por la URL a la que deseas redirigir después de desactivar la cuenta
        else:
            messages.error(request, 'Incorrect password. Please try again.')
    return render(request, 'deactivate_account.html')  # Cambia 'deactivate_account.html' al nombre de tu plantilla
@login_required
def cancel_deactivation(request):
    # Implementar la lógica para cancelar la desactivación si es necesario
    return render(request, 'accounts/cancel_deactivation.html')
