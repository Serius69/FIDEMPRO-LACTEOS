# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/layouts/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from layouts.models import Instructions

class InstructionsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.instructions = Instructions.objects.get(fk_user=self.user)

    def test_instructions_creation(self):
        self.assertEqual(self.instructions.instruction, '')
        self.assertEqual(self.instructions.content, '')
        self.assertEqual(self.instructions.type, 1)
        self.assertEqual(self.instructions.fk_user, self.user)
        self.assertTrue(self.instructions.is_active)

    def test_str_method(self):
        self.assertEqual(str(self.instructions), f"Instructions: {self.instructions.id}")

    def test_create_instructions_signal(self):
        new_user = User.objects.create_user(username='newuser', password='12345')
        new_instructions = Instructions.objects.get(fk_user=new_user)
        self.assertEqual(new_instructions.instruction, '')
        self.assertEqual(new_instructions.content, '')
        self.assertEqual(new_instructions.type, 1)
        self.assertEqual(new_instructions.fk_user, new_user)
        self.assertTrue(new_instructions.is_active)

    def test_save_instructions_signal(self):
        self.user.is_active = False
        self.user.save()
        self.instructions.refresh_from_db()
        self.assertFalse(self.instructions.is_active)