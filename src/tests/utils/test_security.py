import bcrypt
import pytest
import utilities.security as security


def test_hash_password(mocker):
    # Expected result
    password = '1234'
    salt = b'$2b$12$Sz3AvkbAmzPN8elw95os.u'
    expected = bcrypt.hashpw(password.encode('utf-8'), salt).decode()

    # Mock random salt generation for hashing
    mock_gensalt = mocker.patch('bcrypt.gensalt', return_value=salt)

    # Call method under test
    hashed_password = security.hash_password(password)

    # Assertions
    assert mock_gensalt.call_count == 1
    assert hashed_password == expected


@pytest.mark.parametrize(
        'test_password,expected',
        [
            ('password', True),
            ('invalid-password', False),
        ]
    )
def test_validate_password(test_password, expected):
    # Hash password in user table
    password = 'password'
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Call method under test
    checked = security.validate_password(hashed_password.decode(), test_password)

    # Assertions
    assert checked == expected
