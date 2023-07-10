from database.models.user import User
import bcrypt

def test_user(mocker):
    password = '1234'
    salt = b'$2b$12$Sz3AvkbAmzPN8elw95os.u'
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Mock random salt generation for hashing
    mock_gensalt = mocker.patch('bcrypt.gensalt', return_value=salt)

    # Instantiate user
    user = User('John Doe', 'test@testing.com', password, 'user')

    # Validate function calls
    assert mock_gensalt.call_count == 1

    # Validate user fields
    assert user.name == 'John Doe'
    assert user.email == 'test@testing.com'
    assert user.password == hashedPassword
    assert user.role == 'user'

    assert user.__repr__() == '<User: John Doe, email: test@testing.com, role: user>'
