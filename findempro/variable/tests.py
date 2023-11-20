# FILEPATH: /c:/Users/serio/FIDEMPRO-LACTEOS/findempro/variable/tests.py
from django.test import TestCase
from variable.models import Equation, Variable, Area
from sympy import symbols, Eq, solve

class EquationModelTest(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name='Test Area')
        self.variable1 = Variable.objects.create(initials='x', value=1)
        self.variable2 = Variable.objects.create(initials='y', value=2)
        self.equation = Equation.objects.create(
            name='Test Equation',
            expression='variable1 + variable2',
            fk_variable1=self.variable1,
            fk_variable2=self.variable2,
            fk_area=self.area
        )

    def test_equation_creation(self):
        self.assertEqual(self.equation.name, 'Test Equation')
        self.assertEqual(self.equation.expression, 'variable1 + variable2')
        self.assertEqual(self.equation.fk_variable1, self.variable1)
        self.assertEqual(self.equation.fk_variable2, self.variable2)
        self.assertEqual(self.equation.fk_area, self.area)

    def test_calculate_method(self):
        x, y = symbols('x y')
        equation_str = self.equation.expression.replace('variable1', str(self.variable1.initials)).replace('variable2', str(self.variable2.initials))
        equation = Eq(eval(equation_str), 0)
        solution = solve(equation, x, y)
        self.assertEqual(self.equation.calculate(), solution)

    def test_create_equations_signal(self):
        equations_data = [
            {
                'name': 'Test Equation 2',
                'expression': 'variable1 - variable2',
                'variable1': 'x',
                'variable2': 'y',
                'area': 'Test Area'
            }
        ]
        Variable.objects.create(initials='z', value=3, equations_data=equations_data)
        self.assertEqual(Equation.objects.count(), 2)
        self.assertEqual(Equation.objects.last().name, 'Test Equation 2')

    def test_save_equations_signal(self):
        self.variable1.is_active = False
        self.variable1.save()
        self.assertFalse(Equation.objects.get(name='Test Equation').is_active)