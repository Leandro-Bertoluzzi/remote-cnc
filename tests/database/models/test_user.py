from database.models.user import User

def test_user():
    user = User('John Doe', 'test@testing.com', '1234', 'user')

    assert user.name == 'John Doe'
    assert user.email == 'test@testing.com'
    assert user.password == '1234'
    assert user.role == 'user'

    assert user.__repr__() == '<User: John Doe, email: test@testing.com, role: user>'
