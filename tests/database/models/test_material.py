from database.models.material import Material
from datetime import datetime


def test_material():
    # Auxiliary variables
    now = datetime(2023, 7, 20)

    # Instantiate material
    material = Material(name='Example material', description='Just a material', added_at=now)

    # Validate material fields
    assert material.name == 'Example material'
    assert material.description == 'Just a material'
    assert material.added_at == datetime(2023, 7, 20)

    assert material.__repr__() == (
        '<Material: Example material, description: Just a material, added at: 2023-07-20 00:00:00>'
    )
