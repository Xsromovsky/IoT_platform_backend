import jwt
import datetime
import os

SECRET_KEY = os.getenv('SECRET_KEY')
REFRESH_SECRET_KEY = os.getenv('REFRESH_SECRET_KEY')

def generate_session_token(user_id):
    access_token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
            'iat': datetime.datetime.now(datetime.timezone.utc)
        }, SECRET_KEY)
    return access_token

def generate_refresh_token(user_id):
    refresh_token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7),
            'iat': datetime.datetime.now(datetime.timezone.utc)
        }, REFRESH_SECRET_KEY)
    return refresh_token