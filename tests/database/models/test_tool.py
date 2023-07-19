from database.models.tool import Tool
from datetime import datetime

def test_tool():
    # Auxiliary variables
    now = datetime(2023, 7, 20)

    # Instantiate tool
    tool = Tool(name='Example tool', description='Just a tool', added_at=now)

    # Validate tool fields
    assert tool.name == 'Example tool'
    assert tool.description == 'Just a tool'
    assert tool.added_at == datetime(2023, 7, 20)

    assert tool.__repr__() == '<Tool: Example tool, description: Just a tool, added at: 2023-07-20 00:00:00>'

