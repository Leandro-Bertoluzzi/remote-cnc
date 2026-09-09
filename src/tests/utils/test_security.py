import bcrypt
import core.utilities.security as security
import pytest
from jwt import ExpiredSignatureError, InvalidSignatureError


class TestHashPassword:
    def test_hash_password(self, mocker):
        # Expected result
        password = "1234"
        salt = b"$2b$12$Sz3AvkbAmzPN8elw95os.u"
        expected = bcrypt.hashpw(password.encode("utf-8"), salt).decode()

        # Mock random salt generation for hashing
        mock_gensalt = mocker.patch("bcrypt.gensalt", return_value=salt)

        # Call method under test
        hashed_password = security.hash_password(password)

        # Assertions
        assert mock_gensalt.call_count == 1
        assert hashed_password == expected


    @pytest.mark.parametrize(
        "test_password,expected",
        [
            ("password", True),
            ("invalid-password", False),
        ],
    )
    def test_validate_password(self, test_password, expected):
        # Hash password in user table
        password = "password"
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Call method under test
        checked = security.validate_password(hashed_password.decode(), test_password)

        # Assertions
        assert checked == expected


class mydatetime(security.datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return security.datetime.datetime(2050, 12, 30, 18, 0, 0, 0)


class TestToken:
    def test_generate_token(self, monkeypatch):
        # Mock env variables
        monkeypatch.setattr(security, "TOKEN_SECRET", "secret-example")

        # Mock datetime generation
        monkeypatch.setattr(security.datetime, "datetime", mydatetime)

        # Call method under test
        token = security.generate_token(user_id=1)

        # Verify token can be decoded back and contains correct payload
        decoded = security.verify_token(token)
        assert decoded["user_id"] == 1
        assert decoded["exp"] == 2556122400


    def test_verify_token(self, monkeypatch):
        # Manually generated token
        my_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjI1NTYxMjI0MDB9.2ISWda0JDBdD-Ee-7zibI6sVpB5hreinj3k_vLQExDU"  # noqa: E501

        # Mock env variables
        monkeypatch.setattr(security, "TOKEN_SECRET", "secret-example")

        # Call method under test
        data = security.verify_token(my_token)

        # Assertions
        assert data["user_id"] == 1


    def test_verify_token_invalid(self, monkeypatch):
        # Manually generated token with TOKEN_SECRET = 'invalid-secret'
        invalid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjI1NTYxMjI0MDB9.pK9ZAa1s45Y_0VTZiwMdK8g6M-wYYQElm-byutGOXYA"  # noqa: E501

        # Mock env variables
        monkeypatch.setattr(security, "TOKEN_SECRET", "secret-example")

        # Call the method under test and assert exception
        with pytest.raises(InvalidSignatureError) as error:
            security.verify_token(invalid_token)

        # Assertions
        assert "Signature verification failed" in str(error.value)


    def test_verify_token_expired(self, monkeypatch):
        # Manually generated token with an old expiration time
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MDEyODA4NzR9.qUt4b-XmnYbwufIhiFUE64uMGG2zSM6c9rr1bgprqNQ"  # noqa: E501

        # Mock env variables
        monkeypatch.setattr(security, "TOKEN_SECRET", "secret-example")

        # Call the method under test and assert exception
        with pytest.raises(ExpiredSignatureError) as error:
            security.verify_token(expired_token)

        # Assertions
        assert "Signature has expired" in str(error.value)
