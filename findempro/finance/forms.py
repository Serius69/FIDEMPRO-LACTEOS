from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models import FinancialDecision, FinancialDecisionAttachment, FinancialDecisionComment
from business.models import Business


class FinancialDecisionForm(forms.ModelForm):
    """
    Formulario para crear y editar decisiones financieras
    """
    
    class Meta:
        model = FinancialDecision
        fields = [
            'name', 'description', 'amount', 'category', 'priority', 
            'status', 'decision_date', 'implementation_date', 
            'fk_business', 'notes', 'expected_impact', 'risk_assessment', 
            'is_active'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Inversión en equipos de oficina',
                'maxlength': 255,
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe los detalles de esta decisión financiera...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'decision_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'implementation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fk_business': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones, consideraciones especiales, etc...'
            }),
            'expected_impact': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Describe el impacto esperado de esta decisión...'
            }),
            'risk_assessment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Analiza los riesgos asociados...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'name': 'Nombre de la Decisión',
            'description': 'Descripción',
            'amount': 'Monto ($)',
            'category': 'Categoría',
            'priority': 'Prioridad',
            'status': 'Estado',
            'decision_date': 'Fecha de Decisión',
            'implementation_date': 'Fecha de Implementación',
            'fk_business': 'Empresa',
            'notes': 'Notas Adicionales',
            'expected_impact': 'Impacto Esperado',
            'risk_assessment': 'Evaluación de Riesgo',
            'is_active': 'Activo'
        }
        
        help_texts = {
            'name': 'Proporciona un nombre descriptivo para la decisión financiera.',
            'description': 'Opcional. Proporciona detalles adicionales sobre la decisión.',
            'amount': 'Monto asociado a la decisión (opcional).',
            'category': 'Categoriza el tipo de decisión financiera.',
            'priority': 'Nivel de prioridad de la decisión.',
            'status': 'Estado actual de la decisión.',
            'decision_date': 'Fecha en que se tomó la decisión (opcional).',
            'implementation_date': 'Fecha prevista para implementar la decisión.',
            'fk_business': 'Empresa a la que pertenece esta decisión.',
            'notes': 'Información adicional relevante para la decisión.',
            'expected_impact': 'Describe el impacto esperado en el negocio.',
            'risk_assessment': 'Análisis de los riesgos potenciales.',
            'is_active': 'Determina si la decisión está activa o inactiva.'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar solo empresas activas
        self.fields['fk_business'].queryset = Business.objects.filter(is_active=True)
        
        # Si hay una instancia, ajustar algunos campos
        if self.instance and self.instance.pk:
            # Deshabilitar algunos campos si la decisión ya está implementada
            if self.instance.status == 'implementada':
                readonly_fields = ['amount', 'category', 'fk_business']
                for field_name in readonly_fields:
                    if field_name in self.fields:
                        self.fields[field_name].widget.attrs['readonly'] = True
        
        # Personalizar queryset de businesses según el usuario
        if self.user and hasattr(self.user, 'business_permissions'):
            allowed_businesses = self.user.business_permissions.all()
            if allowed_businesses.exists():
                self.fields['fk_business'].queryset = allowed_businesses.filter(is_active=True)

    def clean_name(self):
        """Validación personalizada para el nombre"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 3:
                raise ValidationError('El nombre debe tener al menos 3 caracteres.')
            
            # Verificar duplicados para la misma empresa
            if 'fk_business' in self.cleaned_data:
                business = self.cleaned_data['fk_business']
                existing = FinancialDecision.objects.filter(
                    name__iexact=name,
                    fk_business=business,
                    is_active=True
                )
                
                if self.instance and self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                
                if existing.exists():
                    raise ValidationError(
                        'Ya existe una decisión financiera con este nombre para la empresa seleccionada.'
                    )
        
        return name

    def clean_amount(self):
        """Validación personalizada para el monto"""
        amount = self.cleaned_data.get('amount')
        if amount is not None:
            if amount < 0:
                raise ValidationError('El monto no puede ser negativo.')
            if amount > Decimal('999999999999.99'):
                raise ValidationError('El monto es demasiado grande.')
        return amount

    def clean_decision_date(self):
        """Validación personalizada para la fecha de decisión"""
        decision_date = self.cleaned_data.get('decision_date')
        if decision_date:
            # No permitir fechas futuras muy lejanas
            max_future_date = timezone.now().date().replace(year=timezone.now().year + 1)
            if decision_date > max_future_date:
                raise ValidationError('La fecha de decisión no puede ser más de un año en el futuro.')
        return decision_date

    def clean_implementation_date(self):
        """Validación personalizada para la fecha de implementación"""
        implementation_date = self.cleaned_data.get('implementation_date')
        decision_date = self.cleaned_data.get('decision_date')
        
        if implementation_date:
            # La fecha de implementación no puede ser anterior a la fecha de decisión
            if decision_date and implementation_date < decision_date:
                raise ValidationError(
                    'La fecha de implementación no puede ser anterior a la fecha de decisión.'
                )
        
        return implementation_date

    def clean(self):
        """Validación general del formulario"""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        amount = cleaned_data.get('amount')
        category = cleaned_data.get('category')
        
        # Validaciones específicas según el estado
        if status == 'aprobada' and not amount and category in ['inversion', 'gasto']:
            raise ValidationError(
                'Las decisiones de inversión o gasto aprobadas deben tener un monto especificado.'
            )
        
        # Si el estado es implementada, debe tener fecha de implementación
        if status == 'implementada' and not cleaned_data.get('implementation_date'):
            cleaned_data['implementation_date'] = timezone.now().date()
        
        return cleaned_data

    def save(self, commit=True):
        """Guardar con usuario actual"""
        instance = super().save(commit=False)
        
        if self.user:
            if not instance.pk:  # Nueva instancia
                instance.created_by = self.user
            
            # Establecer usuario actual para auditoría
            from .models import set_current_user
            set_current_user(instance, self.user)
        
        if commit:
            instance.save()
        
        return instance


class FinancialDecisionAttachmentForm(forms.ModelForm):
    """
    Formulario para adjuntos de decisiones financieras
    """
    
    class Meta:
        model = FinancialDecisionAttachment
        fields = ['file', 'name', 'description']
        
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo del archivo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del contenido del archivo'
            })
        }

    def clean_file(self):
        """Validación del archivo"""
        file = self.cleaned_data.get('file')
        if file:
            # Validar tamaño (máximo 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 10 MB.')
            
            # Validar extensiones permitidas
            allowed_extensions = [
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 
                'jpg', 'jpeg', 'png', 'gif', 'txt'
            ]
            
            file_extension = file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise ValidationError(
                    f'Tipo de archivo no permitido. Extensiones permitidas: {", ".join(allowed_extensions)}'
                )
        
        return file


class FinancialDecisionCommentForm(forms.ModelForm):
    """
    Formulario para comentarios en decisiones financieras
    """
    
    class Meta:
        model = FinancialDecisionComment
        fields = ['comment', 'is_internal']
        
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Escribe tu comentario aquí...',
                'required': True
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'comment': 'Comentario',
            'is_internal': 'Comentario Interno'
        }
        
        help_texts = {
            'comment': 'Comparte tu opinión, sugerencia o pregunta sobre esta decisión.',
            'is_internal': 'Marca esta opción si el comentario es solo para usuarios internos.'
        }

    def clean_comment(self):
        """Validación del comentario"""
        comment = self.cleaned_data.get('comment')
        if comment:
            comment = comment.strip()
            if len(comment) < 10:
                raise ValidationError('El comentario debe tener al menos 10 caracteres.')
            if len(comment) > 1000:
                raise ValidationError('El comentario no puede exceder 1000 caracteres.')
        return comment


class FinancialDecisionSearchForm(forms.Form):
    """
    Formulario para búsqueda y filtrado de decisiones financieras
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, descripción o empresa...'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las categorías')] + FinancialDecision.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las prioridades')] + FinancialDecision.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + FinancialDecision.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    business = forms.ModelChoiceField(
        required=False,
        queryset=Business.objects.filter(is_active=True),
        empty_label="Todas las empresas",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )
    
    amount_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Monto mínimo'
        }),
        label='Monto mínimo'
    )
    
    amount_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Monto máximo'
        }),
        label='Monto máximo'
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )

    def clean(self):
        """Validación del formulario de búsqueda"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        amount_min = cleaned_data.get('amount_min')
        amount_max = cleaned_data.get('amount_max')
        
        # Validar rango de fechas
        if date_from and date_to and date_from > date_to:
            raise ValidationError('La fecha "desde" no puede ser posterior a la fecha "hasta".')
        
        # Validar rango de montos
        if amount_min and amount_max and amount_min > amount_max:
            raise ValidationError('El monto mínimo no puede ser mayor al monto máximo.')
        
        return cleaned_data


class BulkActionForm(forms.Form):
    """
    Formulario para acciones en lote
    """
    ACTION_CHOICES = [
        ('', 'Seleccionar acción...'),
        ('delete', 'Eliminar'),
        ('activate', 'Activar'),
        ('deactivate', 'Desactivar'),
        ('change_status', 'Cambiar estado'),
        ('change_priority', 'Cambiar prioridad'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    new_status = forms.ChoiceField(
        choices=FinancialDecision.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    new_priority = forms.ChoiceField(
        choices=FinancialDecision.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    
    selected_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )

    def clean(self):
        """Validación de acciones en lote"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        if action == 'change_status' and not cleaned_data.get('new_status'):
            raise ValidationError('Debe seleccionar un nuevo estado.')
        
        if action == 'change_priority' and not cleaned_data.get('new_priority'):
            raise ValidationError('Debe seleccionar una nueva prioridad.')
        
        return cleaned_data