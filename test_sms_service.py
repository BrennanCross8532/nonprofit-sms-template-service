from src.sms_service import SmsRequest, build_message


def test_receipt_contains_donor_and_amount_variables():
    request = SmsRequest("+15551234567", "receipt", "Mina", "$40")
    assert build_message(request) == {"name": "Mina", "amount": "$40"}
