"""
views/base.py - Vista base y utilidades compartidas
"""
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from django.conf import settings
from django.views.generic import TemplateView
from django.shortcuts import render

logger = logging.getLogger(__name__)


class PagesView(TemplateView):
    """Vista base para páginas estáticas"""
    pass


def get_media_path(relative_path: str) -> str:
    """
    Obtener la ruta completa de un archivo en media
    
    Args:
        relative_path: Ruta relativa dentro de media
        
    Returns:
        Ruta completa del archivo
    """
    return os.path.join(settings.MEDIA_ROOT, relative_path)


def copy_existing_image(source_name: str, dest_folder: str, dest_name: str) -> str:
    """
    Copiar una imagen existente desde la carpeta media o crear un placeholder
    
    Args:
        source_name: Nombre del archivo fuente
        dest_folder: Carpeta destino (relative a media)
        dest_name: Nombre del archivo destino
        
    Returns:
        Ruta relativa del archivo copiado o placeholder
    """
    try:
        # Crear directorio destino si no existe
        dest_dir = os.path.join(settings.MEDIA_ROOT, dest_folder)
        os.makedirs(dest_dir, exist_ok=True)
        
        # Ruta del archivo destino
        dest_path = os.path.join(dest_dir, dest_name)
        
        # Si el archivo destino ya existe, retornar su ruta
        if os.path.exists(dest_path):
            return os.path.join(dest_folder, dest_name)
        
        # Buscar el archivo fuente en diferentes ubicaciones posibles
        possible_sources = [
            os.path.join(settings.MEDIA_ROOT, source_name),
            os.path.join(settings.MEDIA_ROOT, dest_folder, source_name),
            os.path.join(settings.MEDIA_ROOT, 'images', source_name),
            os.path.join(settings.MEDIA_ROOT, 'images', dest_folder, source_name),
        ]
        
        # Añadir rutas estáticas si están configuradas
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            possible_sources.append(os.path.join(settings.STATIC_ROOT, 'images', source_name))
        
        if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
            for static_dir in settings.STATICFILES_DIRS:
                possible_sources.append(os.path.join(static_dir, 'images', source_name))
        
        # Filtrar None values
        possible_sources = [path for path in possible_sources if path]
        
        source_path = None
        
        # Buscar archivo exacto primero
        for path in possible_sources:
            if os.path.exists(path):
                source_path = path
                break
        
        # Si no se encuentra, buscar con diferentes extensiones
        if not source_path:
            extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            name_without_ext = os.path.splitext(source_name)[0]
            
            for ext in extensions:
                for base_path in possible_sources:
                    if base_path:
                        base_dir = os.path.dirname(base_path)
                        test_path = os.path.join(base_dir, name_without_ext + ext)
                        if os.path.exists(test_path):
                            source_path = test_path
                            break
                if source_path:
                    break
        
        # Si se encontró el archivo fuente, copiarlo
        if source_path and os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            logger.info(f"Image copied from {source_path} to {dest_path}")
            return os.path.join(dest_folder, dest_name)
        
        # Si no se puede copiar, crear un placeholder simple
        logger.warning(f"Source image {source_name} not found, creating placeholder")
        create_placeholder_image(dest_path, dest_name)
        return os.path.join(dest_folder, dest_name)
    
    except Exception as e:
        logger.warning(f"Error copying image {source_name}: {str(e)}")
        # Crear placeholder en caso de error
        try:
            dest_dir = os.path.join(settings.MEDIA_ROOT, dest_folder)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, dest_name)
            create_placeholder_image(dest_path, dest_name)
            return os.path.join(dest_folder, dest_name)
        except Exception as e2:
            logger.error(f"Error creating placeholder for {dest_name}: {str(e2)}")
            # Retornar ruta por defecto sin archivo físico
            return os.path.join(dest_folder, dest_name)


def create_placeholder_image(dest_path: str, filename: str) -> None:
    """
    Crear una imagen placeholder simple si PIL está disponible,
    de lo contrario crear un archivo de texto placeholder
    """
    try:
        # Intentar crear imagen con PIL
        from PIL import Image, ImageDraw, ImageFont
        
        # Crear imagen placeholder de 300x200 píxeles
        img = Image.new('RGB', (300, 200), color='#f0f0f0')
        draw = ImageDraw.Draw(img)
        
        # Añadir texto
        try:
            # Intentar usar fuente por defecto
            font = ImageFont.load_default()
        except:
            font = None
        
        text = f"Imagen\n{os.path.splitext(filename)[0]}"
        
        # Calcular posición del texto (centrado)
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width, text_height = 100, 20
        
        x = (300 - text_width) // 2
        y = (200 - text_height) // 2
        
        draw.text((x, y), text, fill='#666666', font=font)
        
        # Guardar imagen
        img.save(dest_path, 'JPEG')
        logger.info(f"Placeholder image created: {dest_path}")
        
    except ImportError:
        # PIL no disponible, crear archivo de texto placeholder
        logger.warning("PIL not available, creating text placeholder")
        create_text_placeholder(dest_path, filename)
    except Exception as e:
        logger.warning(f"Error creating PIL placeholder: {str(e)}, creating text placeholder")
        create_text_placeholder(dest_path, filename)


def create_text_placeholder(dest_path: str, filename: str) -> None:
    """
    Crear un archivo de texto como placeholder
    """
    try:
        placeholder_content = f"""
Placeholder para imagen: {filename}
Creado automáticamente
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Este archivo debe ser reemplazado por la imagen correspondiente.
        """.strip()
        
        # Cambiar extensión a .txt
        text_path = os.path.splitext(dest_path)[0] + '.txt'
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
            
        logger.info(f"Text placeholder created: {text_path}")
        
    except Exception as e:
        logger.error(f"Error creating text placeholder: {str(e)}")


def validate_data_coherence() -> Dict[str, Any]:
    """
    Validar la coherencia entre las diferentes estructuras de datos
    """
    from product.data.products_data import products_data
    from findempro.variable.data.variables_data import variables_data
    from findempro.variable.data.equations_data import equations_data
    
    errors = []
    
    # Validar productos vs variables
    for product in products_data:
        product_vars = [v for v in variables_data if v.get('product') == product['name']]
        if not product_vars:
            errors.append(f"No variables found for product {product['name']}")
            
    # Validar ecuaciones vs variables
    for equation in equations_data:
        for var_name in [equation.get('variable1'), equation.get('variable2')]:
            if var_name and not any(v['initials'] == var_name for v in variables_data):
                errors.append(f"Variable {var_name} not found for equation {equation.get('name')}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


# Vistas de páginas estáticas
def pages_faqs(request):
    """Vista para página de preguntas frecuentes"""
    return render(request, 'pages/faqs.html', {
        'title': 'Preguntas Frecuentes'
    })


def pagina_error_404(request, exception):
    """Vista personalizada para error 404"""
    return render(request, 'pages/404.html', {
        'title': 'Página no encontrada'
    }, status=404)


def pagina_error_500(request):
    """Vista personalizada para error 500"""
    return render(request, 'pages/500.html', {
        'title': 'Error del servidor'
    }, status=500)


# Vistas basadas en clase con context mejorado
class PagesMaintenanceView(PagesView):
    template_name = "pages/maintenance.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sitio en Mantenimiento'
        return context


class PagesComingSoonView(PagesView):
    template_name = "pages/coming-soon.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Próximamente'
        context['launch_date'] = datetime.now() + timedelta(days=30)
        return context


class PagesPrivacyPolicyView(PagesView):
    template_name = "pages/privacy-policy.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Política de Privacidad'
        context['last_updated'] = datetime(2023, 11, 20)
        return context


class PagesTermsConditionsView(PagesView):
    template_name = "pages/term-conditions.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Términos y Condiciones'
        context['last_updated'] = datetime(2023, 11, 20)
        return context


# Instancias de vistas
pages_maintenance = PagesMaintenanceView.as_view()
pages_coming_soon = PagesComingSoonView.as_view()
pages_privacy_policy = PagesPrivacyPolicyView.as_view()
pages_terms_conditions = PagesTermsConditionsView.as_view()