from sqlalchemy.exc import SQLAlchemyError
from database.base import Session
from database.models.file import File
from database.models.user import User

def createFile(userId, fileName, fileNameSaved):
    # Create a new session
    session = Session()

    # Create the file entry
    filePath = f'{userId}/{fileNameSaved}'
    newFile = File(userId, fileName, filePath)

    # Persist data in DB
    session.add(newFile)

    # Commit changes in DB
    try:
        session.commit()
        print('The file was successfully created!')
    except SQLAlchemyError as e:
        raise Exception(f'Error creating the file in the DB: {e}')

    # Close session
    session.close()

    return

def getAllFilesFromUser(user_id):
    # Create a new session
    session = Session()

    # Get data from DB
    try:
        user = session.query(User).get(user_id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for user in the DB: {e}')

    for file in user.files:
            print(f'> {file.user}')
    print('----')

    # Close session
    session.close()

    return user.files

def getAllFiles():
    # Create a new session
    session = Session()

    # Get data from DB
    try:
        files = session.query(File).all()
    except SQLAlchemyError as e:
        raise Exception(f'Error retrieving files from the DB: {e}')

    for file in files:
            print(f'> {file.user}')
    print('----')

    # Close session
    session.close()

    return files

def getFileById(id):
    # Create a new session
    session = Session()

    # Get file from DB
    try:
        file = session.query(File).get(id)
    except SQLAlchemyError as e:
        raise Exception(f'Error looking for file with ID {id} in the DB: {e}')

    if not file:
        raise Exception(f'File with ID {id} was not found')

    return file

def updateFile(id, userId, fileName, fileNameSaved):
    # Create a new session
    session = Session()

    # Get file from DB
    file = getFileById(id)

    # Update the file's info
    file.user_id = userId
    file.file_path = f'{userId}/{fileNameSaved}'
    file.file_name = fileName

    # Commit changes in DB
    try:
        session.commit()
        print('The file was successfully updated!')
    except SQLAlchemyError as e:
        raise Exception(f'Error updating the file in the DB: {e}')

    # Close session
    session.close()

def removeFile(id):
    # Create a new session
    session = Session()

    # Get file from DB
    file = getFileById(id)

    # Remove the file
    session.delete(file)

    # Commit changes in DB
    try:
        session.commit()
        print('The file was successfully removed!')
    except SQLAlchemyError as e:
        raise Exception(f'Error removing the file from the DB: {e}')

    # Close session
    session.close()
