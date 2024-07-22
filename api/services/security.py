from config import TOKEN_SECRET
import datetime
import jwt
from typing import Dict


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


def verify_token(token: str) -> Dict[str, int]:
    return jwt.decode(token, TOKEN_SECRET, algorithms=['HS256'])
