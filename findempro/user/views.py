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

# Create your views here.
# Profile
def profile_product_variable_list_view(request):
    products = Product.objects.all().order_by('-id')
    businesses = Business.objects.all().order_by('-id')
    variables = Variable.objects.all().order_by('-id')
    user = request.user
    profile = UserProfile.objects.get(user=user)
    
    if profile.is_profile_complete():
        completeness_percentage = 100
    else:
        total_fields = len([field for field in profile._meta.get_fields() if field.name != 'id' and field.name != 'user'])
        completed_fields = len([field for field in profile._meta.get_fields() if field.name != 'id' and field.name != 'user' and getattr(profile, field.name)])

        completeness_percentage = (completed_fields / total_fields) * 100
        
    context = {'products': products, 'businesses': businesses, 
               'variables': variables , 'completeness_percentage': completeness_percentage }
    return render(request, 'user/profile.html', context)

# List
def user_list_view(request):
    try:
        users = User.objects.all().order_by('-id')
        context = {'users': users}
        return render(request, 'user/user-list.html', context)
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

# Create
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

# Update
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

# Delete
def delete_user_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    try:
        user.is_active = False
        user.save()
        messages.success(request, "User deleted successfully!")
        return redirect("user:user.list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return HttpResponse(status=500)

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important for maintaining the user's session
            messages.success(request, 'Your password was successfully changed.')
            return redirect('profile')  # Redirect to the user's profile or another appropriate page
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})    
