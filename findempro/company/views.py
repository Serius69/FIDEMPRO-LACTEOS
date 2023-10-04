from django.shortcuts import render, get_object_or_404
from .models import Company, CompanyProduct
from product.models import Product
# View for listing all companies
def company_list(request):
    companies = Company.objects.all()
    context = {'companies': companies}
    return render(request, 'company/company-list.html.html', context)

# View for displaying company details
def company_detail(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    products = CompanyProduct.objects.filter(company=company)
    return render(request, 'apps/company/company-overview.html', {'company': company, 'products': products})

# View for managing company products (add/remove)
def manage_company_products(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    
    if request.method == 'POST':
        # Add a product to the company's products
        product_id = request.POST.get('product_id')
        if product_id:
            product = get_object_or_404(Product, id=product_id)
            CompanyProduct.objects.get_or_create(company=company, product=product)
        
        # Remove a product from the company's products
        remove_product_id = request.POST.get('remove_product_id')
        if remove_product_id:
            CompanyProduct.objects.filter(company=company, product__id=remove_product_id).delete()
    
    products = CompanyProduct.objects.filter(company=company)
    return render(request, 'company/manage_company_products.html', {'company': company, 'products': products})
