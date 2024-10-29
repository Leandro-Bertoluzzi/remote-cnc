import pytest
import utilities.security as security
from jwt import ExpiredSignatureError, InvalidSignatureError


class mydatetime(security.datetime.datetime):
    @classmethod
    def now(cls):
        return security.datetime.datetime(2050, 12, 30, 18, 0, 0, 0)


def test_generate_token(monkeypatch):
    # Manually generated token
    expected_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjI1NTYxMjI0MDB9.2ISWda0JDBdD-Ee-7zibI6sVpB5hreinj3k_vLQExDU'  # noqa: E501

    # Mock env variables
    monkeypatch.setattr(security, 'TOKEN_SECRET', 'secret-example')

    # Mock datetime generation
    monkeypatch.setattr(security.datetime, 'datetime', mydatetime)

    # Call method under test
    token = security.generate_token(user_id=1)

    # Assertions
    assert token == expected_token


def test_verify_token(monkeypatch):
    # Manually generated token
    my_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjI1NTYxMjI0MDB9.2ISWda0JDBdD-Ee-7zibI6sVpB5hreinj3k_vLQExDU'  # noqa: E501

    # Mock env variables
    monkeypatch.setattr(security, 'TOKEN_SECRET', 'secret-example')

    # Call method under test
    data = security.verify_token(my_token)

    # Assertions
    assert data['user_id'] == 1


def test_verify_token_invalid(monkeypatch):
    # Manually generated token with TOKEN_SECRET = 'invalid-secret'
    invalid_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjI1NTYxMjI0MDB9.pK9ZAa1s45Y_0VTZiwMdK8g6M-wYYQElm-byutGOXYA'  # noqa: E501

    # Mock env variables
    monkeypatch.setattr(security, 'TOKEN_SECRET', 'secret-example')

    # Call the method under test and assert exception
    with pytest.raises(InvalidSignatureError) as error:
        security.verify_token(invalid_token)

    # Assertions
    assert 'Signature verification failed' in str(error.value)


def test_verify_token_expired(monkeypatch):
    # Manually generated token with an old expiration time
    expired_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MDEyODA4NzR9.qUt4b-XmnYbwufIhiFUE64uMGG2zSM6c9rr1bgprqNQ'  # noqa: E501

    # Mock env variables
    monkeypatch.setattr(security, 'TOKEN_SECRET', 'secret-example')

    # Call the method under test and assert exception
    with pytest.raises(ExpiredSignatureError) as error:
        security.verify_token(expired_token)

    # Assertions
    assert 'Signature has expired' in str(error.value)
