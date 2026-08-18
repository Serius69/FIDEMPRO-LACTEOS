from modeling.engine import ModelCompileError
from modeling.errors import decode_error, encode_error, simulation_error
from modeling.safe_expression import ExpressionError


def test_simulation_error_is_actionable_without_internal_exception_text():
    detail = simulation_error(ModelCompileError({"errors": [{"path": "equations[profit]", "code": "cycle", "message": "Dependencia circular."}]}))

    assert detail["code"] == "invalid_model"
    assert detail["where"] == "equations[profit]"
    assert detail["how_to_fix"]
    assert "traceback" not in encode_error(detail).lower()


def test_expression_and_unknown_errors_have_safe_public_messages():
    expression = simulation_error(ExpressionError("private implementation detail"))
    unknown = simulation_error(RuntimeError("database password=secret"))

    assert expression["code"] == "invalid_expression"
    assert "private implementation" not in encode_error(expression)
    assert "database password" not in encode_error(unknown)
    assert decode_error(encode_error(unknown))["code"] == "simulation_failed"
