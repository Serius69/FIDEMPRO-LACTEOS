import pytest
from django.utils import timezone
from django.contrib.auth.models import User
from questionary.models import Questionary, QuestionaryResult, Question, Answer
from business.models import Business
from product.models import Product
from variable.models import Variable


def _build_chain(suffix=""):
    """Crea la cadena User -> Business -> Product que exige el esquema vigente."""
    user = User.objects.create_user(username=f"tester{suffix}", password="password")
    business = Business.objects.create(
        name=f"Test Business {suffix}",
        type=1,
        location="La Paz",
        description="Negocio de prueba",
        fk_user=user,
        is_active=True,
    )
    product = Product.objects.create(
        fk_business=business,
        name=f"Test Product {suffix}",
        description="d",
        is_active=True,
    )
    return user, business, product


@pytest.mark.django_db
def test_questionary_creation():
    _, _, product = _build_chain("q")
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
    _, _, product = _build_chain("r")
    questionary = Questionary.objects.create(
        questionary="Test Questionary",
        fk_product=product
    )
    questionary_result = QuestionaryResult.objects.create(
        fk_questionary=questionary,
        is_active=True,
        date_created=timezone.now(),
    )
    assert questionary_result.fk_questionary == questionary
    assert questionary_result.is_active is True

@pytest.mark.django_db
def test_question_creation():
    _, _, product = _build_chain("qu")
    variable = Variable.objects.create(name="Test Variable", fk_product=product)
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
    _, _, product = _build_chain("a")
    variable = Variable.objects.create(name="Test Variable", fk_product=product)
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
