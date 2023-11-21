from database.models.tool import Tool
from database.repositories.toolRepository import ToolRepository
import pytest
from sqlalchemy.exc import SQLAlchemyError


class TestToolRepository:
    def test_create_tool(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)
        name = 'New Tool'
        description = 'A new tool'

        # Call method under test
        new_tool = tool_repository.create_tool(name, description)

        # Assertions
        assert new_tool is not None
        assert isinstance(new_tool, Tool)
        assert new_tool.id is not None
        assert new_tool.description == description

    def test_get_all_tools(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)

        # Call method under test
        tools = tool_repository.get_all_tools()

        # Assertions
        assert isinstance(tools, list)

    def test_get_tool_by_id(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)

        # Call method under test
        tool = tool_repository.get_tool_by_id(1)

        # Assertions
        assert isinstance(tool, Tool)
        assert tool.name == 'tool 1'
        assert tool.description == 'It is a tool'

    def test_update_tool(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)
        updated_name = 'Updated Tool'
        updated_description = 'Updated description'

        # Call method under test
        updated_tool = tool_repository.update_tool(1, updated_name, updated_description)

        # Assertions
        assert updated_tool.name == updated_name
        assert updated_tool.description == updated_description

    def test_remove_tool(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)
        tools_before = tool_repository.get_all_tools()

        # Call method under test
        tool_repository.remove_tool(id=1)

        # Assertions
        tools_after = tool_repository.get_all_tools()
        assert len(tools_after) == len(tools_before) - 1

    def test_error_create_tool_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'add', side_effect=SQLAlchemyError('mocked error'))
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.create_tool(name='name', description='description')
        assert 'Error creating the tool in the DB' in str(error.value)

    def test_error_get_all_tools_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'query', side_effect=SQLAlchemyError('mocked error'))
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.get_all_tools()
        assert 'Error retrieving tools from the DB' in str(error.value)

    def test_error_get_non_existing_tool(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.get_tool_by_id(id=5000)
        assert str(error.value) == 'Tool with ID 5000 was not found'

    def test_error_get_tool_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'query', side_effect=SQLAlchemyError('mocked error'))
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.get_tool_by_id(id=1)
        assert 'Error retrieving the tool with ID 1' in str(error.value)

    def test_error_update_non_existing_tool(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.update_tool(id=5000, name='name', description='description')
        assert str(error.value) == 'Tool with ID 5000 was not found'

    def test_error_update_tool_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'query', side_effect=SQLAlchemyError('mocked error'))
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.update_tool(id=1, name='name', description='description')
        assert 'Error updating the tool in the DB' in str(error.value)

    def test_error_remove_non_existing_tool(self, mocked_session):
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.remove_tool(id=5000)
        assert str(error.value) == 'Tool with ID 5000 was not found'

    def test_error_remove_tool_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'query', side_effect=SQLAlchemyError('mocked error'))
        tool_repository = ToolRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            tool_repository.remove_tool(id=1)
        assert 'Error removing the tool from the DB' in str(error.value)
