import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from questionary.models import Questionary, Question, Answer, QuestionaryResult
from business.models import Business
from product.models import Product

"""
Test for the questionnaire update view using the PUT method.

This test verifies that the `questionnaire_update_view` correctly updates an
existing answer associated with a questionnaire result when provided with valid
data.

Args:
    client: Django test client used to simulate HTTP requests.
    user: A user instance used for authentication.
    questionary_result: A questionnaire result instance associated with the answer.

Setup:
    - Logs in the test user.
    - Creates an `Answer` instance linked to the provided `questionary_result`.

Test Steps:
    1. Constructs the URL for the `questionnaire_update_view` using the IDs of
       the `questionary_result` and the `Answer`.
    2. Sends a PUT request with JSON data containing the updated answer.
    3. Asserts that the response status code is 200 (OK).
    4. Refreshes the `Answer` instance from the database.
    5. Asserts that the `answer` field of the `Answer` instance has been updated
       to the new value.

Expected Outcome:
    - The `Answer` instance's `answer` field is updated to "Updated Answer".
"""
@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="password")

@pytest.fixture
def business(user):
    return Business.objects.create(name="Test Business", is_active=True, fk_user=user)

@pytest.fixture
def product(business):
    return Product.objects.create(name="Test Product", is_active=True, fk_business=business)

@pytest.fixture
def questionary(product):
    return Questionary.objects.create(name="Test Questionary", is_active=True, fk_product=product)

@pytest.fixture
def question(questionary):
    return Question.objects.create(question="Test Question", is_active=True, fk_questionary=questionary)

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
    assert response.context["selected_questionary_id"] == str(questionary.id)

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
def test_questionnaire_update_view_put(client, user, questionary_result):
    client.login(username="testuser", password="password")
    answer = Answer.objects.create(
        fk_questionary_result=questionary_result,
        answer="Old Answer"
    )
    url = reverse("questionary:questionnaire_update_view", args=[questionary_result.id, answer.id])
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
    url = reverse("questionary:questionnaire_result_view", args=[questionary_result.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "questionary_result" in response.context
    assert response.context["questionary_result"] == questionary_result

@pytest.mark.django_db
def test_questionary_list_view(client, user, questionary_result):
    client.login(username="testuser", password="password")
    url = reverse("questionary:questionary_list_view")
    response = client.get(url)
    assert response.status_code == 200
    assert "questionary_results" in response.context
    assert questionary_result in response.context["questionary_results"]
    
    
    