from sqlalchemy.exc import SQLAlchemyError
from database.base import Session
from database.models.user import User, VALID_ROLES

def createUser(name, email, password, role):
    # Create a new session
    session = Session()

    # Validates the input
    if role not in VALID_ROLES:
        raise Exception(f'ERROR: Role {role} is not valid')

    # Checks the use doesn't exist in DB
    user = session.query(User).filter_by(email=email).first()
    if user:
        raise Exception(f'There is already a user registered with the email {email}')

    # Create the user
    newUser = User(name, email, password, role)

    # Persist data in DB
    session.add(newUser)

    # Commit changes in DB
    try:
        session.commit()
        print('The user was successfully created!')
    except SQLAlchemyError as e:
        raise Exception(f'Error creating the user in the DB: {e}')

    # Close session
    session.close()

    return

def getAllUsers():
    # Create a new session
    session = Session()

    # Get data from DB
    users = []
    try:
        users = session.query(User).all()
    except SQLAlchemyError as e:
        raise Exception(f'Error retrieving users from the DB: {e}')

    # Close session
    session.close()

    return users

def updateUser(id, name, email, role):
    # Create a new session
    session = Session()

    # Validates the input
    if role not in VALID_ROLES:
        raise Exception(f'ERROR: Role {role} is not valid')

    # Get user from DB
    try:
        user = session.query(User).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for user in the DB: {e}')

    if not user:
        raise Exception(f'User with ID {id} was not found')

    # Update the user's info
    user.name = name
    user.email = email
    user.role = role

    # Commit changes in DB
    try:
        session.commit()
        print('The user was successfully updated!')
    except SQLAlchemyError as e:
        raise Exception(f'Error updating the user in the DB: {e}')

    # Close session
    session.close()

def removeUser(id):
    # Create a new session
    session = Session()

    # Get user from DB
    try:
        user = session.query(User).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for user in the DB: {e}')

    if not user:
        raise Exception(f'User with ID {id} was not found')

    # Remove the user
    session.delete(user)

    # Commit changes in DB
    try:
        session.commit()
        print('The user was successfully removed!')
    except SQLAlchemyError as e:
        raise Exception(f'Error removing the user from the DB: {e}')

    # Close session
    session.close()
