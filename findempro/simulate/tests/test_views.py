import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth.models import User
from simulate.models import Simulation, ResultSimulation, Demand, ProbabilisticDensityFunction
from questionary.models import QuestionaryResult, Answer
from product.models import Product, Area
from business.models import Business
from findempro.simulate.codeall import plot_scatter_and_pdf
import numpy as np
from findempro.simulate.codeall import plot_histogram_and_pdf
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from simulate.models import Simulation, ProbabilisticDensityFunction
from questionary.models import QuestionaryResult
from product.models import Product

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpassword')

@pytest.fixture
def business(user):
    return Business.objects.create(name="Test Business", is_active=True, fk_user=user)

@pytest.fixture
def product(business):
    return Product.objects.create(name="Test Product", is_active=True, fk_business=business)

@pytest.fixture
def questionary_result(product):
    return QuestionaryResult.objects.create(is_active=True, fk_questionary=product)

@pytest.fixture
def probabilistic_density_function(business):
    return ProbabilisticDensityFunction.objects.create(
        distribution_type=1,  # Normal distribution
        mean_param=0,
        std_dev_param=1,
        lambda_param=1,
        is_active=True,
        fk_business=business
    )

@pytest.mark.django_db
def test_simulate_show_view_get(client, user, business, product, questionary_result):
    client.login(username='testuser', password='testpassword')
    url = reverse('simulate:simulate.show')
    response = client.get(url)
    assert response.status_code == 200
    assert 'simulate/simulate-init.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_simulate_show_view_post_start(client, user, business, product, questionary_result, probabilistic_density_function):
    client.login(username='testuser', password='testpassword')
    url = reverse('simulate:simulate.show')
    data = {
        'start': 'start',
        'fk_questionary_result': questionary_result.id,
        'quantity_time': 10,
        'unit_time': 'days',
        'demand_history': '[100, 200, 300]',
        'fk_fdp': probabilistic_density_function.id,
    }
    response = client.post(url, data)
    assert response.status_code == 302  # Redirect
    assert Simulation.objects.filter(fk_questionary_result=questionary_result).exists()

@pytest.mark.django_db
def test_simulate_show_view_post_cancel(client, user):
    client.login(username='testuser', password='testpassword')
    url = reverse('simulate:simulate.show')
    data = {'cancel': 'cancel'}
    response = client.post(url, data)
    assert response.status_code == 302  # Redirect

@pytest.mark.django_db
def test_simulate_result_simulation_view(client, user, business, product, questionary_result):
    client.login(username='testuser', password='testpassword')
    simulation = Simulation.objects.create(
        fk_questionary_result=questionary_result,
        quantity_time=10,
        unit_time='days',
        demand_history='[100, 200, 300]',
        is_active=True
    )
    url = reverse('simulate:simulate.result', args=[simulation.id])
    response = client.get(url)
    assert response.status_code == 200
    assert 'simulate/simulate-result.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_plot_scatter_and_pdf():
    data = np.random.normal(0, 1, 100)
    pdf = np.random.normal(0, 1, 100)
    result = plot_scatter_and_pdf(data, pdf, "Normal Distribution")
    assert isinstance(result, str)  # Should return a base64 string

@pytest.mark.django_db
def test_plot_histogram_and_pdf():
    data = np.random.normal(0, 1, 100)
    pdf = np.random.normal(0, 1, 100)
    result = plot_histogram_and_pdf(data, pdf, "Normal Distribution")
    assert isinstance(result, str)  # Should return a base64 string
    
# TESTS FOR SIMULATION VIEW USABILITY
class TestSimulateShowViewUsability(StaticLiveServerTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.business = Business.objects.create(name="Test Business", is_active=True, fk_user=self.user)
        self.product = Product.objects.create(name="Test Product", is_active=True, fk_business=self.business)
        self.questionary_result = QuestionaryResult.objects.create(is_active=True, fk_questionary=self.product)
        self.probabilistic_density_function = ProbabilisticDensityFunction.objects.create(
            distribution_type=1,  # Normal distribution
            mean_param=0,
            std_dev_param=1,
            lambda_param=1,
            is_active=True,
            fk_business=self.business
        )
        self.url = self.live_server_url + reverse('simulate:simulate.show')
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()

    def test_navigation_to_simulate_show_view(self):
        self.driver.get(self.url)
        self.assertIn("Simulación", self.driver.title)

    def test_form_submission_success(self):
        self.driver.get(self.url)
        self.driver.find_element(By.NAME, "username").send_keys("testuser")
        self.driver.find_element(By.NAME, "password").send_keys("testpassword")
        self.driver.find_element(By.NAME, "login").click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "simulate-form"))
        )

        self.driver.find_element(By.NAME, "fk_questionary_result").send_keys(self.questionary_result.id)
        self.driver.find_element(By.NAME, "quantity_time").send_keys("10")
        self.driver.find_element(By.NAME, "unit_time").send_keys("days")
        self.driver.find_element(By.NAME, "demand_history").send_keys("[100, 200, 300]")
        self.driver.find_element(By.NAME, "fk_fdp").send_keys(self.probabilistic_density_function.id)
        self.driver.find_element(By.NAME, "start").click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        success_message = self.driver.find_element(By.CLASS_NAME, "success-message").text
        self.assertIn("Simulación iniciada con éxito", success_message)

    def test_form_submission_error(self):
        self.driver.get(self.url)
        self.driver.find_element(By.NAME, "username").send_keys("testuser")
        self.driver.find_element(By.NAME, "password").send_keys("testpassword")
        self.driver.find_element(By.NAME, "login").click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "simulate-form"))
        )

        self.driver.find_element(By.NAME, "fk_questionary_result").send_keys("")
        self.driver.find_element(By.NAME, "quantity_time").send_keys("")
        self.driver.find_element(By.NAME, "unit_time").send_keys("")
        self.driver.find_element(By.NAME, "demand_history").send_keys("")
        self.driver.find_element(By.NAME, "fk_fdp").send_keys("")
        self.driver.find_element(By.NAME, "start").click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        error_message = self.driver.find_element(By.CLASS_NAME, "error-message").text
        self.assertIn("Por favor, complete todos los campos", error_message)

    def test_cancel_button_functionality(self):
        self.driver.get(self.url)
        self.driver.find_element(By.NAME, "username").send_keys("testuser")
        self.driver.find_element(By.NAME, "password").send_keys("testpassword")
        self.driver.find_element(By.NAME, "login").click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "simulate-form"))
        )

        self.driver.find_element(By.NAME, "cancel").click()

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "info-message"))
        )
        info_message = self.driver.find_element(By.CLASS_NAME, "info-message").text
        self.assertIn("Simulación cancelada", info_message)