"""
Automated checks. Run with:  python -m pytest tests

A test is a small piece of code that checks another piece of code does
what we promised. If someone changes the anonymiser later and breaks it,
these tests fail and tell us straight away.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anonymise import anonymise_text  # noqa: E402
from split import find_template_groups, normalise  # noqa: E402


def test_masks_local_phone_number():
    assert anonymise_text("send to 0244123456 now") == "send to <PHONE> now"


def test_masks_international_phone_number():
    assert "<PHONE>" in anonymise_text("call +233 24 412 3456")


def test_masks_transaction_id():
    assert anonymise_text("Transaction ID 71234567890") == "Transaction ID <LONG_NUMBER>"


def test_masks_capital_name_in_momo_alert():
    assert anonymise_text("received from KWAME ASANTE.") == "received from <NAME>."


def test_keeps_company_name():
    # One capital word is a company, not a person, so it stays
    assert anonymise_text("payment to ECG was successful") == "payment to ECG was successful"


def test_keeps_amounts():
    # Amounts are useful to the model and not personal, so they stay
    assert "GHS 500" in anonymise_text("you have received GHS 500")


def test_normalise_makes_amounts_identical():
    assert normalise("Send GHS 200 now!") == normalise("send ghs 500 NOW")


def test_near_copies_share_a_group():
    texts = [
        "I mistakenly send GHS 200 to your number, kindly send it back",
        "I mistakenly send GHS 500 to your number, kindly send it back",
        "Are we still meeting tomorrow at 4pm?",
    ]
    groups = find_template_groups(texts)
    assert groups[0] == groups[1]
    assert groups[0] != groups[2]
