"""Regression tests for the policy condition evaluator (replaces eval(); review finding F2)."""

import pytest

from app.core.safe_expression import UnsafeExpressionError, evaluate_condition

CTX = {
    "price_bdt": 60_000_000,
    "location": "Banani",
    "action": "SEND_MESSAGE",
    "confidence": 0.7,
    "discount_amount_bdt": 600_000,
    "property_price": 100,
    "verified_database_price": 120,
    "tags": ["vip", "hot"],
}


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("price_bdt > 50000000 and location == 'Banani'", True),
        ("price_bdt > 50000000 and location == 'Gulshan'", False),
        ("action == 'SEND_MESSAGE' and confidence < 0.85", True),
        ("action == 'SEND_OFFER' and discount_amount_bdt > 500000", False),
        ("property_price != verified_database_price", True),
        ("not (confidence >= 0.85)", True),
        ("0.5 < confidence < 0.8", True),
        ("'vip' in tags", True),
        ("location not in ['Gulshan', 'Dhanmondi']", True),
        ("price_bdt - discount_amount_bdt > 59000000", True),
        ("confidence < 0.5 or location == 'Banani'", True),
    ],
)
def test_allowed_expressions(expression, expected):
    assert evaluate_condition(expression, CTX) is expected


@pytest.mark.parametrize(
    "expression",
    [
        # The sandbox escape that eval(expr, {"__builtins__": None}) allowed
        "().__class__.__base__.__subclasses__()",
        "().__class__.__base__.__subclasses__()[0].__name__ == 'type'",
        "[c for c in ().__class__.__mro__]",
        "__import__('os')",
        "open('/etc/passwd')",
        "(lambda: 1)()",
        "tags[0] == 'vip'",
        "location.upper() == 'BANANI'",
        "2 ** 999999",
        "confidence is None",
        "x := 1",
    ],
)
def test_disallowed_constructs_rejected(expression):
    with pytest.raises(UnsafeExpressionError):
        evaluate_condition(expression, CTX)


def test_unknown_variable_rejected():
    with pytest.raises(UnsafeExpressionError):
        evaluate_condition("missing_var > 1", CTX)


def test_private_context_keys_not_exposed():
    with pytest.raises(UnsafeExpressionError):
        evaluate_condition("_secret == 1", {"_secret": 1})


def test_length_and_complexity_limits():
    with pytest.raises(UnsafeExpressionError):
        evaluate_condition("confidence > 0 and " * 100 + "True", CTX)
    with pytest.raises(UnsafeExpressionError):
        evaluate_condition("", CTX)


async def test_simulate_policy_endpoint_contract():
    from app.services.ai_control_plane.control_plane_service import control_plane_service

    ok = await control_plane_service.simulate_policy("confidence < 0.85", {"confidence": 0.5})
    assert ok["success"] is True and ok["triggered"] is True

    blocked = await control_plane_service.simulate_policy("().__class__.__base__.__subclasses__()", {})
    assert blocked["success"] is False and blocked["triggered"] is False
