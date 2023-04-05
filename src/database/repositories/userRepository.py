import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from database.base import Session, Base
from database.models.user import User, VALID_ROLES

def createUser(name, email, password, role):
    # Create a new session
    session = Session()

    # Validates the input
    if role not in VALID_ROLES:
        print(f'ERROR: Role {role} is not valid')
        return

    # --- Encrypt password ---
    # Adding the salt to password
    salt = bcrypt.gensalt()
    # Hashing the password
    hashedPassword = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Create the user
    newUser = User(name, email, hashedPassword, role)

    # Persist data in DB
    session.add(newUser)

    # Commit changes in DB
    try:
        session.commit()
    except SQLAlchemyError as e:
        print(e)

    print('The user was successfully created!')

    # Close session
    session.close()