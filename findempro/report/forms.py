from django import forms
from django.core.exceptions import ValidationError
from .models import Report
from product.models import Product
import json

class ReportForm(forms.ModelForm):
    """Formulario para crear y editar reportes"""
    
    class Meta:
        model = Report
        fields = ['title', 'content', 'fk_product', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el título del reporte'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Contenido del reporte (JSON format)'
            }),
            'fk_product': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Título del Reporte',
            'content': 'Contenido',
            'fk_product': 'Producto Asociado',
            'is_active': 'Activo'
        }
        help_texts = {
            'title': 'Nombre descriptivo para el reporte',
            'content': 'Contenido en formato JSON',
            'fk_product': 'Seleccione el producto asociado (opcional)',
            'is_active': 'Marque si el reporte debe estar activo'
        }

    def clean_content(self):
        """Validar que el contenido sea JSON válido"""
        content = self.cleaned_data['content']
        if isinstance(content, str):
            try:
                json.loads(content)
            except json.JSONDecodeError:
                raise ValidationError("El contenido debe ser un JSON válido")
        return content

class SimulationReportForm(forms.Form):
    """Formulario para crear reportes basados en simulaciones"""
    
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Producto para Simulación',
        help_text='Seleccione el producto para el cual generar la simulación'
    )
    
    # Parámetros de simulación
    demanda_inicial = forms.IntegerField(
        min_value=1,
        initial=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1000'
        }),
        label='Demanda Inicial',
        help_text='Demanda inicial en unidades'
    )
    
    tasa_crecimiento = forms.DecimalField(
        min_value=0,
        max_value=100,
        decimal_places=2,
        initial=5.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '5.0',
            'step': '0.01'
        }),
        label='Tasa de Crecimiento (%)',
        help_text='Tasa de crecimiento anual esperada'
    )
    
    horizonte = forms.IntegerField(
        min_value=1,
        max_value=120,
        initial=12,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '12'
        }),
        label='Horizonte de Tiempo (meses)',
        help_text='Período de simulación en meses'
    )
    
    precio_unitario = forms.DecimalField(
        min_value=0.01,
        decimal_places=2,
        initial=100.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '100.00',
            'step': '0.01'
        }),
        label='Precio Unitario',
        help_text='Precio de venta por unidad'
    )
    
    costo_unitario = forms.DecimalField(
        min_value=0.01,
        decimal_places=2,
        initial=60.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '60.00',
            'step': '0.01'
        }),
        label='Costo Unitario',
        help_text='Costo variable por unidad'
    )
    
    gastos_fijos = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        initial=5000.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '5000.00',
            'step': '0.01'
        }),
        label='Gastos Fijos Mensuales',
        help_text='Gastos fijos mensuales'
    )
    
    inversion_inicial = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        initial=50000.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '50000.00',
            'step': '0.01'
        }),
        label='Inversión Inicial',
        help_text='Inversión inicial requerida'
    )
    
    tipo_simulacion = forms.ChoiceField(
        choices=[
            ('basica', 'Simulación Básica'),
            ('avanzada', 'Simulación Avanzada'),
            ('montecarlo', 'Simulación Monte Carlo'),
        ],
        initial='basica',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Simulación',
        help_text='Seleccione el tipo de simulación a realizar'
    )
    
    incluir_graficas = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Incluir Gráficas',
        help_text='Generar gráficas en el reporte'
    )
    
    incluir_analisis_sensibilidad = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Análisis de Sensibilidad',
        help_text='Incluir análisis de sensibilidad de variables'
    )

    def clean(self):
        """Validaciones adicionales del formulario"""
        cleaned_data = super().clean()
        precio = cleaned_data.get('precio_unitario')
        costo = cleaned_data.get('costo_unitario')
        
        if precio and costo and precio <= costo:
            raise ValidationError(
                "El precio unitario debe ser mayor al costo unitario para tener margen de ganancia."
            )
        
        return cleaned_data

    def get_simulation_params(self):
        """Obtiene los parámetros de simulación como diccionario"""
        if self.is_valid():
            return {
                'demanda_inicial': self.cleaned_data['demanda_inicial'],
                'tasa_crecimiento': float(self.cleaned_data['tasa_crecimiento']),
                'horizonte': self.cleaned_data['horizonte'],
                'precio_unitario': float(self.cleaned_data['precio_unitario']),
                'costo_unitario': float(self.cleaned_data['costo_unitario']),
                'gastos_fijos': float(self.cleaned_data['gastos_fijos']),
                'inversion_inicial': float(self.cleaned_data['inversion_inicial']),
                'tipo_simulacion': self.cleaned_data['tipo_simulacion'],
                'incluir_graficas': self.cleaned_data['incluir_graficas'],
                'incluir_analisis_sensibilidad': self.cleaned_data['incluir_analisis_sensibilidad'],
            }
        return {}

class ReportSearchForm(forms.Form):
    """Formulario para buscar reportes"""
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar reportes...',
            'id': 'search-input'
        }),
        label='Buscar'
    )
    
    product_filter = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        required=False,
        empty_label="Todos los productos",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Filtrar por Producto'
    )
    
    status_filter = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('active', 'Activos'),
            ('inactive', 'Inactivos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
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

class BulkReportActionForm(forms.Form):
    """Formulario para acciones en lote sobre reportes"""
    
    action = forms.ChoiceField(
        choices=[
            ('activate', 'Activar'),
            ('deactivate', 'Desactivar'),
            ('delete', 'Eliminar'),
            ('export', 'Exportar'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Acción'
    )
    
    selected_reports = forms.CharField(
        widget=forms.HiddenInput(),
        label='Reportes Seleccionados'
    )
    
    def clean_selected_reports(self):
        """Validar que se hayan seleccionado reportes"""
        selected = self.cleaned_data['selected_reports']
        if not selected:
            raise ValidationError("Debe seleccionar al menos un reporte")
        
        try:
            report_ids = [int(id_str) for id_str in selected.split(',')]
            if not Report.objects.filter(id__in=report_ids).exists():
                raise ValidationError("Algunos reportes seleccionados no existen")
            return report_ids
        except ValueError:
            raise ValidationError("IDs de reportes inválidos")