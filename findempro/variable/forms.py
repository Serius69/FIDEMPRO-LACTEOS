from django import forms
from .models import Variable, Equation
from business.models import Business
from product.models import Product, Area

class VariableForm(forms.ModelForm):
    class Meta:
        model = Variable
        fields = ('name', 'type', 'unit', 'description', 'image_src', 'fk_product')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la variable'
            }),
            'type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                ('L', 'L'),
                ('Bs', 'Bs'),
                ('Lt/Bs', 'Lt/Bs'),
            ]),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description'
            }),
            'image_src': forms.FileInput(attrs={
                'class': 'form-control d-none',
                'accept': 'image/png, image/jpeg'
            }),
            'fk_product': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter products based on user's businesses
            businesses = Business.objects.filter(is_active=True, fk_user=user)
            self.fields['fk_product'].queryset = Product.objects.filter(
                is_active=True, 
                fk_business__in=businesses
            )

class EquationForm(forms.ModelForm):
    class Meta:
        model = Equation
        fields = ['name', 'description', 'expression', 'fk_variable1', 'fk_variable2', 
                 'fk_variable3', 'fk_variable4', 'fk_variable5', 'fk_area']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la ecuación'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingrese la descripción'
            }),
            'expression': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'var1=var2+var3'
            }),
            'fk_variable1': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fk_variable2': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fk_variable3': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fk_variable4': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fk_variable5': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fk_area': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter variables based on user's businesses
            businesses = Business.objects.filter(is_active=True, fk_user=user)
            products = Product.objects.filter(is_active=True, fk_business__in=businesses)
            variables_queryset = Variable.objects.filter(
                is_active=True, 
                fk_product__in=products
            )
            
            # Apply the filtered queryset to all variable fields
            for field_name in ['fk_variable1', 'fk_variable2', 'fk_variable3', 'fk_variable4', 'fk_variable5']:
                self.fields[field_name].queryset = variables_queryset
                if field_name != 'fk_variable1':  # Make all except first variable optional
                    self.fields[field_name].required = False
            
            # Filter areas based on user's products
            self.fields['fk_area'].queryset = Area.objects.filter(
                is_active=True,
                fk_product__in=products
            )
            self.fields['fk_area'].required = False  # Make area optional