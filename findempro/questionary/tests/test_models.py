import pytest
from django.utils import timezone
from findempro.questionary.models import Questionary, QuestionaryResult, Question, Answer
from product.models import Product
from variable.models import Variable

@pytest.mark.django_db
def test_questionary_creation():
    product = Product.objects.create(name="Test Product")
    questionary = Questionary.objects.create(
        questionary="Test Questionary",
        fk_product=product,
        is_active=True,
        date_created=timezone.now(),
        last_updated=timezone.now()
    )
    assert questionary.questionary == "Test Questionary"
    assert questionary.fk_product == product
    assert questionary.is_active is True

@pytest.mark.django_db
def test_questionary_result_creation():
    product = Product.objects.create(name="Test Product")
    questionary = Questionary.objects.create(
        questionary="Test Questionary",
        fk_product=product
    )
    questionary_result = QuestionaryResult.objects.create(
        fk_questionary=questionary,
        is_active=True,
        date_created=timezone.now(),
        last_updated=timezone.now()
    )
    assert questionary_result.fk_questionary == questionary
    assert questionary_result.is_active is True

@pytest.mark.django_db
def test_question_creation():
    product = Product.objects.create(name="Test Product")
    variable = Variable.objects.create(name="Test Variable")
    questionary = Questionary.objects.create(
        questionary="Test Questionary",
        fk_product=product
    )
    question = Question.objects.create(
        question="What is your favorite color?",
        fk_questionary=questionary,
        fk_variable=variable,
        type=1,
        possible_answers={"options": ["Red", "Blue", "Green"]},
        is_active=True,
        date_created=timezone.now(),
        last_updated=timezone.now()
    )
    assert question.question == "What is your favorite color?"
    assert question.fk_questionary == questionary
    assert question.fk_variable == variable
    assert question.type == 1
    assert question.possible_answers == {"options": ["Red", "Blue", "Green"]}
    assert question.is_active is True

@pytest.mark.django_db
def test_answer_creation():
    product = Product.objects.create(name="Test Product")
    variable = Variable.objects.create(name="Test Variable")
    questionary = Questionary.objects.create(
        questionary="Test Questionary",
        fk_product=product
    )
    questionary_result = QuestionaryResult.objects.create(
        fk_questionary=questionary
    )
    question = Question.objects.create(
        question="What is your favorite color?",
        fk_questionary=questionary,
        fk_variable=variable
    )
    answer = Answer.objects.create(
        answer="Blue",
        fk_question=question,
        fk_questionary_result=questionary_result,
        is_active=True,
        date_created=timezone.now(),
        last_updated=timezone.now()
    )
    assert answer.answer == "Blue"
    assert answer.fk_question == question
    assert answer.fk_questionary_result == questionary_result
    assert answer.is_active is True
    

