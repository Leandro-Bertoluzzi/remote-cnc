import bcrypt


# Passwords

def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode()


def validate_password(hash: str, test: str) -> bool:
    return bcrypt.checkpw(test.encode('utf-8'), hash.encode('utf-8'))
