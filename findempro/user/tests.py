# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/user/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from user.models import UserProfile

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user_profile = UserProfile.objects.get(user=self.user)

    def test_user_profile_creation(self):
        self.assertEqual(self.user_profile.user, self.user)
        self.assertEqual(self.user_profile.bio, '')
        self.assertEqual(self.user_profile.state, '')
        self.assertEqual(self.user_profile.country, '')
        self.assertEqual(self.user_profile.image_src, 'images/users/user-dummy-img.webp')

    def test_get_photo_url(self):
        self.assertEqual(self.user_profile.get_photo_url(), '/media/images/users/user-dummy-img.webp')

    def test_is_profile_complete(self):
        self.assertFalse(self.user_profile.is_profile_complete())
        self.user_profile.bio = 'Test Bio'
        self.user_profile.state = 'Test State'
        self.user_profile.country = 'Test Country'
        self.user_profile.save()
        self.assertTrue(self.user_profile.is_profile_complete())