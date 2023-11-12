from questionary.models import Questionary,Question   # Reemplaza 'your_app' con el nombre de tu aplicación.

for data in questionary_data:
    Questionary.objects.create(**data)


for data in question_data:
    Question.objects.create(**data)
    