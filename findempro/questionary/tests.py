# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/questionary/tests.py
from django.test import TestCase
from questionary.models import Question, Questionary, Variable

class QuestionModelTest(TestCase):
    def setUp(self):
        self.questionary = Questionary.objects.create(name='Test Questionary')
        self.variable = Variable.objects.create(name='Test Variable')
        self.question = Question.objects.create(
            question='Test Question',
            fk_questionary=self.questionary,
            fk_variable=self.variable,
            type=1,
            is_active=True
        )

    def test_question_creation(self):
        self.assertEqual(self.question.question, 'Test Question')
        self.assertEqual(self.question.fk_questionary, self.questionary)
        self.assertEqual(self.question.fk_variable, self.variable)
        self.assertEqual(self.question.type, 1)
        self.assertTrue(self.question.is_active)

    def test_create_question_function(self):
        new_questionary = Questionary.objects.create(name='New Questionary')
        new_variable = Variable.objects.create(name='New Variable')
        question_data = [
            {
                'question': 'New Question',
                'type': 1,
                'initials_variable': new_variable.name,
            }
        ]
        Question.create_question(Questionary, new_questionary, True, question_data=question_data)
        new_question = Question.objects.get(question='New Question')
        self.assertIsNotNone(new_question)
        self.assertEqual(new_question.fk_questionary, new_questionary)
        self.assertEqual(new_question.fk_variable, new_variable)

    def test_save_question_method(self):
        self.questionary.is_active = False
        self.questionary.save()
        self.question.refresh_from_db()
        self.assertFalse(self.question.is_active)