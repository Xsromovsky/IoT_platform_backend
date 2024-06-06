from functools import wraps
from flask import request, jsonify
import jwt
from app.models import User

SECRET_KEY = 'your_secret_key'
REFRESH_SECRET_KEY = 'your_refresh_secret_key'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            if token.startswith('Bearer '):
                token = token.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 403

        return f(current_user, *args, **kwargs)

    return decorated

def refresh_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'Message': 'Refresh token is missing'}), 403
        
        try:
            data = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'Message': 'Refresh token has expired'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'Message': 'Refresh token is invalid'}), 403
        
        return f(current_user, *args, **kwargs)
    return decorated