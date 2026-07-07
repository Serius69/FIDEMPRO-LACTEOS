# findempro/forms.py
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import FormActions
from allauth.account.forms import (
    LoginForm, SignupForm, ChangePasswordForm, 
    ResetPasswordForm, ResetPasswordKeyForm, SetPasswordForm
)
from django import forms
from django.utils.translation import gettext_lazy as _

class UserLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        # Personalizar campos
        self.fields['login'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Usuario o Email'),
            'autofocus': True
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Contraseña')
        })
        if 'remember' in self.fields:
            self.fields['remember'].widget.attrs.update({
                'class': 'form-check-input'
            })

class UserRegistrationForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        
        # Personalizar campos
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Correo electrónico')
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Nombre de usuario')
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Contraseña')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirmar contraseña')
        })
        
        # Personalizar labels
        self.fields['email'].label = _("Correo Electrónico")
        self.fields['username'].label = _("Usuario")
        self.fields['password1'].label = _("Contraseña")
        self.fields['password2'].label = _("Confirmar Contraseña")

class PasswordChangeForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        
        self.fields['oldpassword'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Contraseña actual')
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Nueva contraseña')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirmar nueva contraseña')
        })
        
        self.fields['oldpassword'].label = _("Contraseña Actual")
        self.fields['password1'].label = _("Nueva Contraseña")
        self.fields['password2'].label = _("Confirmar Nueva Contraseña")

class PasswordResetForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Correo electrónico'),
            'autofocus': True
        })
        self.fields['email'].label = _("Correo Electrónico")

class PasswordResetKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetKeyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Nueva contraseña')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirmar nueva contraseña')
        })
        
        self.fields['password1'].label = _("Nueva Contraseña")
        self.fields['password2'].label = _("Confirmar Contraseña")

class PasswordSetForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(PasswordSetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Nueva contraseña')
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirmar contraseña')
        })
        
        self.fields['password1'].label = _("Contraseña")
        self.fields['password2'].label = _("Confirmar Contraseña")