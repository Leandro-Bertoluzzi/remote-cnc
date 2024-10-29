import bcrypt
import datetime
import jwt
from config import TOKEN_SECRET


# Passwords

def hash_password(password: str) -> str:
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode()


def validate_password(hash: str, test: str) -> bool:
    return bcrypt.checkpw(test.encode('utf-8'), hash.encode('utf-8'))


# JSON Web Token
def generate_token(user_id: int) -> str:
    return jwt.encode(
        {
            'user_id': user_id,
            'exp': datetime.datetime.now() + datetime.timedelta(1)
        },
        TOKEN_SECRET,
        algorithm='HS256'
    )


def verify_token(token: str) -> dict[str, int]:
    return jwt.decode(token, TOKEN_SECRET, algorithms=['HS256'])
