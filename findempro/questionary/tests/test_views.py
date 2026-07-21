import json

import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from questionary.models import Questionary, Question, Answer, QuestionaryResult
from business.models import Business
from product.models import Product
from variable.models import Variable

"""
Tests de las vistas del cuestionario contra el esquema vigente.

La cadena de objetos requerida es:
    User -> Business(type, location, description) -> Product(description)
    -> Questionary(questionary=...) -> Question(fk_variable=...) / QuestionaryResult

Los nombres de URL reales viven en questionary/urls.py (app_name='questionary'):
    questionary.main / questionary.list / questionary.result / questionary.update_answer
"""


@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def business(user):
    return Business.objects.create(
        name="Test Business",
        type=1,
        location="La Paz",
        description="Negocio de prueba",
        fk_user=user,
        is_active=True,
    )

@pytest.fixture
def product(business):
    return Product.objects.create(
        fk_business=business,
        name="Test Product",
        description="d",
        is_active=True,
    )

@pytest.fixture
def variable(product):
    return Variable.objects.create(name="Test Variable", fk_product=product)

@pytest.fixture
def questionary(product):
    return Questionary.objects.create(questionary="Test Questionary", is_active=True, fk_product=product)

@pytest.fixture
def question(questionary, variable):
    return Question.objects.create(
        question="Test Question",
        is_active=True,
        fk_questionary=questionary,
        fk_variable=variable,
    )

@pytest.fixture
def questionary_result(questionary):
    return QuestionaryResult.objects.create(fk_questionary=questionary)

@pytest.mark.django_db
def test_questionnaire_main_view_get(client, user, questionary, question):
    client.login(username="testuser", password="password")
    url = reverse("questionary:questionary.main")
    response = client.get(url, {"select": True, "selected_questionary_id": questionary.id})
    assert response.status_code == 200
    assert "selected_questionary_id" in response.context
    # La vista guarda el id como entero en el contexto.
    assert response.context["selected_questionary_id"] == questionary.id

@pytest.mark.django_db
def test_questionnaire_main_view_post_start(client, user, questionary):
    client.login(username="testuser", password="password")
    session = client.session
    session["selected_questionary_id"] = questionary.id
    session.save()
    url = reverse("questionary:questionary.main")
    response = client.post(url, {"start": True})
    assert response.status_code == 302
    assert "questionary_result_id" in client.session

@pytest.mark.django_db
def test_questionnaire_main_view_post_save(client, user, questionary, question, questionary_result):
    client.login(username="testuser", password="password")
    session = client.session
    session["selected_questionary_id"] = questionary.id
    session["questionary_result_id"] = questionary_result.id
    session.save()
    url = reverse("questionary:questionary.main")
    response = client.post(url, {
        f"question_{question.id}": question.id,
        f"answer_{question.id}": "Test Answer",
        "save": True
    })
    assert response.status_code == 302
    assert Answer.objects.filter(fk_question=question, answer="Test Answer").exists()

@pytest.mark.django_db
def test_post_save_upsert_does_not_duplicate(client, user, questionary, question, questionary_result):
    """Re-guardar la misma pregunta actualiza la fila, no crea un duplicado."""
    client.login(username="testuser", password="password")
    session = client.session
    session["selected_questionary_id"] = questionary.id
    session["questionary_result_id"] = questionary_result.id
    session.save()
    url = reverse("questionary:questionary.main")

    payload = {
        f"question_{question.id}": question.id,
        f"answer_{question.id}": "Primera",
        "save": True,
    }
    client.post(url, payload)
    payload[f"answer_{question.id}"] = "Segunda"
    client.post(url, payload)

    answers = Answer.objects.filter(
        fk_question=question, fk_questionary_result=questionary_result
    )
    assert answers.count() == 1
    assert answers.first().answer == "Segunda"


@pytest.mark.django_db
def test_post_save_reactivates_inactive_answer(client, user, questionary, question, questionary_result):
    """Re-guardar una answer previamente desactivada la deja is_active=True."""
    client.login(username="testuser", password="password")
    # Simula el estado tras cancelar/borrar: answer existente pero inactiva.
    Answer.objects.create(
        fk_question=question,
        fk_questionary_result=questionary_result,
        answer="Borrador",
        is_active=False,
    )
    session = client.session
    session["selected_questionary_id"] = questionary.id
    session["questionary_result_id"] = questionary_result.id
    session.save()
    url = reverse("questionary:questionary.main")

    client.post(url, {
        f"question_{question.id}": question.id,
        f"answer_{question.id}": "Reactivada",
        "save": True,
    })

    answers = Answer.objects.filter(
        fk_question=question, fk_questionary_result=questionary_result
    )
    assert answers.count() == 1
    ans = answers.first()
    assert ans.is_active is True
    assert ans.answer == "Reactivada"


@pytest.mark.django_db
def test_questionnaire_main_view_post_cancel(client, user):
    client.login(username="testuser", password="password")
    session = client.session
    session["started_questionary"] = True
    session.save()
    url = reverse("questionary:questionary.main")
    response = client.post(url, {"cancel": True})
    assert response.status_code == 302
    assert not client.session.get("started_questionary", False)

@pytest.mark.django_db
def test_questionnaire_update_view_put(client, user, question, questionary_result):
    client.login(username="testuser", password="password")
    answer = Answer.objects.create(
        fk_question=question,
        fk_questionary_result=questionary_result,
        answer="Old Answer"
    )
    url = reverse("questionary:questionary.update_answer", args=[questionary_result.id, answer.id])
    response = client.put(url, data=json.dumps({
        "answerId": answer.id,
        "resultId": questionary_result.id,
        "new_answer": "Updated Answer"
    }), content_type="application/json")
    assert response.status_code == 200
    answer.refresh_from_db()
    assert answer.answer == "Updated Answer"

@pytest.mark.django_db
def test_questionnaire_result_view(client, user, questionary_result):
    client.login(username="testuser", password="password")
    url = reverse("questionary:questionary.result", args=[questionary_result.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "questionary_result" in response.context
    assert response.context["questionary_result"] == questionary_result

@pytest.mark.django_db
def test_questionary_list_view(client, user, questionary_result):
    client.login(username="testuser", password="password")
    url = reverse("questionary:questionary.list")
    response = client.get(url)
    assert response.status_code == 200
    assert "questionary_results" in response.context
    assert questionary_result in response.context["questionary_results"]
