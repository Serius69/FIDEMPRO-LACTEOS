from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from user.models import User
from .data_instructions import data_instructions
import logging

logger = logging.getLogger(__name__)


class Instructions(models.Model):
    """
    Modelo para almacenar instrucciones del sistema por usuario
    """
    INSTRUCTION_TYPES = (
        (1, _('General')),
        (2, _('Financiera')),
        (3, _('Técnica')),
        (4, _('Operativa')),
    )
    
    instruction = models.TextField(
        _('Instrucción'),
        help_text=_('Título o resumen de la instrucción'),
        blank=True, 
        null=True
    )
    
    content = models.TextField(
        _('Contenido'),
        help_text=_('Contenido detallado de las instrucciones'),
        blank=True, 
        null=True
    )
    
    type = models.IntegerField(
        _('Tipo'),
        default=1,
        choices=INSTRUCTION_TYPES,
        help_text=_('El tipo de instrucción')
    )
    
    fk_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_instructions',  # Cambiado de 'fk_user_instructions'
        verbose_name=_('Usuario'),
        help_text=_('El usuario asociado con las instrucciones')
    )
    
    is_active = models.BooleanField(
        _('Activo'),
        default=True,
        help_text=_('Si las instrucciones están activas o no')
    )
    
    date_created = models.DateTimeField(
        _('Fecha de Creación'),
        auto_now_add=True,
        help_text=_('La fecha en que se crearon las instrucciones')
    )
    
    last_updated = models.DateTimeField(
        _('Última Actualización'),
        auto_now=True,  # Cambiado de auto_now_add a auto_now
        help_text=_('La fecha de la última actualización')
    )
    
    order = models.IntegerField(
        _('Orden'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Orden de visualización de las instrucciones')
    )

    def __str__(self):
        return f"{self.get_type_display()}: {self.instruction[:50]}..."

    class Meta:
        verbose_name = _('Instrucción')
        verbose_name_plural = _('Instrucciones')
        ordering = ['order', 'type', 'date_created']
        indexes = [
            models.Index(fields=['fk_user', 'is_active']),
            models.Index(fields=['type', 'order']),
        ]
        
    def get_short_content(self, length=100):
        """
        Retorna una versión resumida del contenido
        
        Args:
            length: Longitud máxima del resumen
            
        Returns:
            str: Contenido resumido
        """
        if self.content and len(self.content) > length:
            return f"{self.content[:length]}..."
        return self.content or ""
        
    def activate(self):
        """Activar la instrucción"""
        self.is_active = True
        self.save(update_fields=['is_active', 'last_updated'])
        
    def deactivate(self):
        """Desactivar la instrucción"""
        self.is_active = False
        self.save(update_fields=['is_active', 'last_updated'])


@receiver(post_save, sender=User)
def create_user_instructions(sender, instance, created, **kwargs):
    """
    Crear instrucciones predeterminadas cuando se crea un nuevo usuario
    """
    if created:
        try:
            instructions_created = []
            
            for index, data in enumerate(data_instructions):
                # Validar datos antes de crear
                if not data.get('instruction'):
                    logger.warning(f"Skipping instruction with no title at index {index}")
                    continue
                    
                instruction = Instructions.objects.create(
                    instruction=data.get('instruction', ''),
                    content=data.get('content', ''),
                    type=data.get('type', 1),
                    fk_user=instance,
                    order=data.get('order', index),
                    is_active=True
                )
                instructions_created.append(instruction)
            
            logger.info(
                f"Created {len(instructions_created)} instructions for user {instance.id}"
            )
            
        except Exception as e:
            logger.error(
                f"Error creating instructions for user {instance.id}: {str(e)}"
            )


@receiver(post_save, sender=User)
def update_user_instructions_status(sender, instance, **kwargs):
    """
    Actualizar el estado de las instrucciones cuando cambia el estado del usuario
    """
    if not kwargs.get('created', False):
        try:
            # Actualizar todas las instrucciones del usuario
            updated_count = instance.user_instructions.update(
                is_active=instance.is_active
            )
            
            if updated_count > 0:
                logger.info(
                    f"Updated {updated_count} instructions for user {instance.id} "
                    f"to active={instance.is_active}"
                )
                
        except Exception as e:
            logger.error(
                f"Error updating instructions status for user {instance.id}: {str(e)}"
            )