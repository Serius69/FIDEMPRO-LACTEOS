from django.db import models
from django.utils import timezone
from product.models import Product
from business.models import Business
from variable.models import Variable
from django.db.models.signals import post_save
from django.dispatch import receiver
from .questionary_data import questionary_data,question_data
from .questionary_result_data import questionary_result_data, answer_data
from django.core.exceptions import MultipleObjectsReturned
from django.http import Http404
class Questionary(models.Model):
    questionary = models.CharField(max_length=255)
    fk_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='fk_product_questionary', 
        help_text='The product associated with the questionnaire',
        default=1)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.questionary
    @receiver(post_save, sender=Product)
    def create_questionary(sender, instance, created, **kwargs):
        if created:
            for data in questionary_data:  # Assuming products_data is defined somewhere
                Questionary.objects.create(
                    questionary=f"{data['questionary']} {instance.name}",
                    fk_product=instance,
                    is_active=True
                )
    @receiver(post_save, sender=Product)
    def save_questionary(sender, instance, **kwargs):
        for questionary in instance.fk_product_questionary.all():
            questionary.is_active = instance.is_active
            questionary.save()
class QuestionaryResult(models.Model):
    fk_questionary = models.ForeignKey(
        Questionary, 
        on_delete=models.CASCADE, 
        related_name='fk_questionary_questionary_result',
        help_text='The questionnaire associated with the question',
        default=1
    )
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the question was created')
    last_updated = models.DateTimeField(default=timezone.now, help_text='The date the question was last updated')

    @receiver(post_save, sender=Questionary)
    def create_or_update_questionary_result(sender, instance, created, **kwargs):
        # Evitar crear o actualizar si es una instancia existente
        if not created:
            return

        # Intentar obtener un objeto existente
        questionary_result = QuestionaryResult.objects.filter(fk_questionary=instance).first()

        # Si no existe, crear uno
        if not questionary_result:
            questionary_result = QuestionaryResult.objects.create(
                fk_questionary=instance,
                is_active=instance.is_active
            )
        else:
            # Si existe, actualizar el estado
            questionary_result.is_active = instance.is_active
            questionary_result.save()

class Question(models.Model):
    question = models.TextField()
    fk_questionary = models.ForeignKey(
        Questionary, 
        on_delete=models.CASCADE, 
        related_name='fk_questionary_question',
        help_text='The questionnaire associated with the question'
        )
    fk_variable = models.ForeignKey(
        Variable, 
        on_delete=models.CASCADE, 
        related_name='fk_variable_question',
        help_text='The variable associated with the question'
        )
    type = models.IntegerField(default=1, help_text='The type of question')
    possible_answers = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text='The status of the question')
    date_created = models.DateTimeField(default=timezone.now, help_text='The date the question was created')
    last_updated = models.DateTimeField(default=timezone.now, help_text='The date the question was last updated')

    def __str__(self):
        return self.question
    @receiver(post_save, sender=Questionary)
    def create_question(sender, instance, created, **kwargs):
        questionary = Questionary.objects.get(pk=instance.pk)
        if created:
            for data in question_data:
                try:
                    variable = Variable.objects.get(initials=data['initials_variable'])
                except MultipleObjectsReturned:
                    variable = Variable.objects.filter(initials=data['initials_variable']).first()

                if data['type'] == 1:
                    possible_answers = None  # Default value if 'possible_answers' is not present
                else:
                    possible_answers = data.get('possible_answers')
                    
                Question.objects.create(
                    question=data['question'],
                    type=data['type'],
                    fk_questionary_id=instance.id,
                    fk_variable_id=variable.id,
                    possible_answers=possible_answers,
                    is_active=True
                )
            # hay que hacer que tambien se creen las preguntas de tipo 2
            def create_answer(instance):
                questionary_result = QuestionaryResult.objects.create(
                    fk_questionary=instance,
                    is_active=True
                )
                for data in answer_data:
                    def get_question(question):
                            try:
                                if question == None:
                                    return None
                                return Question.objects.get(question=question)
                            except Question.DoesNotExist:
                                raise Http404(f"question with question '{question}' does not exist.")
                            except Question.MultipleObjectsReturned:
                                return Question.objects.filter(question=question).first()
                        
                    question = get_question(data['question'])
                    Answer.objects.create(
                        answer=data['answer'],
                        fk_question=question,
                        fk_questionary_result=questionary_result,
                            is_active=True
                        )
            questions_created = Question.objects.filter(fk_questionary_id=questionary.id).count()
            total_questions_expected = len(question_data)
            print(questions_created)
            print(total_questions_expected)
            if questions_created == total_questions_expected:
                print(f"Todas las preguntas se han creado correctamente para el producto {questionary.id}.")
                create_answer(instance)
            else:
                print(f"No se han creado todas las preguntas para el cuestionario {questionary.id}.")
    @receiver(post_save, sender=Questionary)
    def save_question(sender, instance, **kwargs):
        for question in instance.fk_questionary_question.all():
            question.is_active = instance.is_active
            question.save()
class Answer(models.Model):
    answer = models.TextField()
    fk_question = models.ForeignKey(
        Question, on_delete=models.CASCADE, 
        related_name='fk_question_answer', help_text='The question associated with the answer', default=1)
    fk_questionary_result = models.ForeignKey(
        QuestionaryResult, on_delete=models.CASCADE, related_name='fk_question_result_answer', 
        help_text='The questionary result associated with the answer', default=1)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.answer
    # @receiver(post_save, sender=QuestionaryResult)
    # def create_answer(sender, instance, created, **kwargs):
    #     if created:
    #         for data in answer_data:
    #             def get_variable(question):
    #                         try:
    #                             if question == None:
    #                                 return None
    #                             return Question.objects.get(question=question)
    #                         except Question.DoesNotExist:
    #                             raise Http404(f"question with question '{question}' does not exist.")
    #                         except Question.MultipleObjectsReturned:
    #                             return Question.objects.filter(question=question).first()
                
    #             question = get_variable(data['question'])
    #             Answer.objects.create(
    #                     answer=data['answer'],
    #                     fk_question=question,
    #                     fk_questionary_result=instance,
    #                     is_active=True
    #                 )
                               
    # @receiver(post_save, sender=QuestionaryResult)
    def save_answer(instance, **kwargs):
        for answer in instance.fk_question_answer.all():
            answer.is_active = instance.is_active
            answer.save()