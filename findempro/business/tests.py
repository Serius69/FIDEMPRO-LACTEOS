# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/business/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from business.models import Business

class BusinessModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', password='12345')
        self.business = Business.objects.create(
            name='Test Business',
            type=1,
            location='Test Location',
            fk_user=self.user
        )

    def test_business_creation(self):
        self.assertEqual(self.business.name, 'Test Business')
        self.assertEqual(self.business.type, 1)
        self.assertEqual(self.business.location, 'Test Location')
        self.assertEqual(self.business.fk_user, self.user)

    def test_get_photo_url_method(self):
        self.assertEqual(self.business.get_photo_url(), "/static/images/business/business-dummy-img.webp")

    def test_create_business_signal(self):
        new_user = User.objects.create(username='newuser', password='12345')
        business = Business.objects.filter(fk_user=new_user)
        self.assertEqual(business.count(), 1)
        self.assertEqual(business.first().name, 'Pyme Lactea')
        self.assertEqual(business.first().type, 1)
        self.assertEqual(business.first().location, 'La Paz')

    def test_save_business_signal(self):
        self.user.is_active = False
        self.user.save()
        self.assertFalse(Business.objects.get(fk_user=self.user).is_active)