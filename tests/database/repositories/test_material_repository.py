from database.models.material import Material
from database.repositories.materialRepository import MaterialRepository
import pytest
from sqlalchemy.exc import SQLAlchemyError


class TestMaterialRepository:
    def test_create_material(self, mocked_session):
        material_repository = MaterialRepository(mocked_session)
        name = 'New Material'
        description = 'A new material'

        # Call method under test
        new_material = material_repository.create_material(name, description)

        # Assertions
        assert new_material is not None
        assert isinstance(new_material, Material)
        assert new_material.id is not None
        assert new_material.description == description

    def test_get_all_materials(self, mocked_session):
        material_repository = MaterialRepository(mocked_session)

        # Call method under test
        materials = material_repository.get_all_materials()

        # Assertions
        assert isinstance(materials, list)

    def test_update_material(self, mocked_session):
        material_repository = MaterialRepository(mocked_session)
        updated_name = 'Updated Material'
        updated_description = 'Updated description'

        # Call method under test
        updated_material = material_repository.update_material(
            1,
            updated_name,
            updated_description
        )

        # Assertions
        assert updated_material.name == updated_name
        assert updated_material.description == updated_description

    def test_remove_material(self, mocked_session):
        material_repository = MaterialRepository(mocked_session)
        materials_before = material_repository.get_all_materials()

        # Call method under test
        material_repository.remove_material(id=1)

        # Assertions
        materials_after = material_repository.get_all_materials()
        assert len(materials_after) == len(materials_before) - 1

    def test_error_create_material_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'add', side_effect=SQLAlchemyError('mocked error'))
        material_repository = MaterialRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            material_repository.create_material(name='name', description='description')
        assert 'Error creating the material in the DB' in str(error.value)

    def test_error_get_all_materials_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'query', side_effect=SQLAlchemyError('mocked error'))
        material_repository = MaterialRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            material_repository.get_all_materials()
        assert 'Error retrieving materials from the DB' in str(error.value)

    def test_error_update_non_existing_material(self, mocked_session):
        material_repository = MaterialRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            material_repository.update_material(id=5000, name='name', description='description')
        assert str(error.value) == 'Material with ID 5000 was not found'

    def test_error_update_material_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'query', side_effect=SQLAlchemyError('mocked error'))
        material_repository = MaterialRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            material_repository.update_material(id=1, name='name', description='description')
        assert 'Error updating the material in the DB' in str(error.value)

    def test_error_remove_non_existing_material(self, mocked_session):
        material_repository = MaterialRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            material_repository.remove_material(id=5000)
        assert str(error.value) == 'Material with ID 5000 was not found'

    def test_error_remove_material_db_error(self, mocker, mocked_session):
        # Mock DB method to simulate exception
        mocker.patch.object(mocked_session, 'query', side_effect=SQLAlchemyError('mocked error'))
        material_repository = MaterialRepository(mocked_session)

        # Call the method under test and assert exception
        with pytest.raises(Exception) as error:
            material_repository.remove_material(id=1)
        assert 'Error removing the material from the DB' in str(error.value)
