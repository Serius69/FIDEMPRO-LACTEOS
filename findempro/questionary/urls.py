from django.urls import path
from . import views

app_name = 'questionary'

urlpatterns = [
    # Vista principal del cuestionario
    path('', views.questionnaire_main_view, name='questionary.main'),
    
    # Lista de cuestionarios completados
    path('list/', views.questionary_list_view, name='questionary.list'),
    
    # Ver resultado de un cuestionario
    path('result/<int:pk>/', views.questionnaire_result_view, name='questionary.result'),
    
    # Editar un cuestionario completo
    path('edit/<int:pk>/', views.questionnaire_edit_view, name='questionary.edit'),
    
    # Eliminar un cuestionario
    path('delete/<int:pk>/', views.questionnaire_delete_view, name='questionary.delete'),
    
    # Actualizar una respuesta individual (AJAX)
    path('result/<int:result_id>/questionary/update_question_view/<int:answer_id>/', 
         views.questionnaire_update_view, name='questionary.update_answer'),
    
    # Buscar respuesta (AJAX)
    path('find_answer/<int:answer_id>/', views.find_answer, name='questionary.find_answer'),
]