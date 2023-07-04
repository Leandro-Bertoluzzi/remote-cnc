import pytest

from database.models.user import User

class TestUsersRepository:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        pass

    def test_create_user(self, qtbot):
        pass
