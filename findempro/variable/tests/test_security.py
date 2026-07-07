"""
Tests de seguridad para `variable.views.solve_equation`.

Regresión del RCE: la vista usaba `eval()` sobre `request.POST['equation']`.
Se reemplazó por `_validar_expresion_matematica` (lista blanca) + `sympy.parse_expr`.
`parse_expr`/`sympify` por sí solos NO son seguros (permiten `().__class__...` →
escape de sandbox), por eso la validación estricta previa es imprescindible.
"""
import pytest

from variable.views import _validar_expresion_matematica as validar


EXPRESIONES_VALIDAS = [
    'x**2 - 4',
    'x + 3.5',
    '2*x - 8',
    'sin(x) - 0.5',
    'sqrt(x) - 2',
    'exp(x) - 1',
    '(x - 1)*(x + 1)',
]

PAYLOADS_MALICIOSOS = [
    '().__class__.__bases__[0].__subclasses__()',
    '__import__("os").system("id")',
    'x.__class__',
    'os.system("touch /tmp/pwned")',
    'open("/etc/passwd").read()',
    'x[0]',
    'eval("1+1")',
    'lambda: 1',
    '{}.__class__',
]


@pytest.mark.parametrize('expr', EXPRESIONES_VALIDAS)
def test_expresiones_matematicas_validas_se_aceptan(expr):
    assert validar(expr) == expr


@pytest.mark.parametrize('payload', PAYLOADS_MALICIOSOS)
def test_payloads_maliciosos_se_rechazan(payload):
    with pytest.raises(ValueError):
        validar(payload)


def test_expresion_vacia_se_rechaza():
    with pytest.raises(ValueError):
        validar('')


def test_expresion_demasiado_larga_se_rechaza():
    with pytest.raises(ValueError):
        validar('x+' * 300)
