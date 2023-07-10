from sqlalchemy.exc import SQLAlchemyError
from database.base import Session
from database.models.material import Material

def createMaterial(name, description):
    # Create a new session
    session = Session()

    # Create the material
    newMaterial = Material(name, description)

    # Persist data in DB
    session.add(newMaterial)

    # Commit changes in DB
    try:
        session.commit()
        print('The material was successfully created!')
    except SQLAlchemyError as e:
        raise Exception(f'Error creating the material in the DB: {e}')

    # Close session
    session.close()

    return

def getAllMaterials():
    # Create a new session
    session = Session()

    # Get data from DB
    materials = []
    try:
        materials = session.query(Material).all()
    except SQLAlchemyError as e:
        raise Exception(f'Error retrieving materials from the DB: {e}')

    # Close session
    session.close()

    return materials

def updateMaterial(id, name, description):
    # Create a new session
    session = Session()

    # Get material from DB
    try:
        material = session.query(Material).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for material in the DB: {e}')

    if not material:
        raise Exception(f'Material with ID {id} was not found')

    # Update the material's info
    material.name = name
    material.description = description

    # Commit changes in DB
    try:
        session.commit()
        print('The material was successfully updated!')
    except SQLAlchemyError as e:
        raise Exception(f'Error updating the material in the DB: {e}')

    # Close session
    session.close()

def removeMaterial(id):
    # Create a new session
    session = Session()

    # Get material from DB
    try:
        material = session.query(Material).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for material in the DB: {e}')

    if not material:
        raise Exception(f'Material with ID {id} was not found')

    # Remove the material
    session.delete(material)

    # Commit changes in DB
    try:
        session.commit()
        print('The material was successfully removed!')
    except SQLAlchemyError as e:
        raise Exception(f'Error removing the material from the DB: {e}')

    # Close session
    session.close()
