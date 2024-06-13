from flask import Blueprint, request, jsonify
# from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from app.auth import token_required, refresh_token_required
# from app.utils.dev_token_generator import generate_api_token
from app.utils.user_token_generator import generate_refresh_token, generate_session_token


bp_user = Blueprint('user_routes', __name__)


@bp_user.route('/')
def home():
    return "Hello, world!"


@bp_user.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password_hash(password):
            return jsonify({'message': 'Invalid credentials'}), 401

        # access_token = jwt.encode({
        #     'user_id': user.id,
        #     'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
        #     'iat': datetime.datetime.now(datetime.timezone.utc)
        # }, SECRET_KEY)

        # refresh_token = jwt.encode({
        #     'user_id': user.id,
        #     'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7),
        #     'iat': datetime.datetime.now(datetime.timezone.utc)
        # }, REFRESH_SECRET_KEY)

        access_token = generate_session_token(user_id=user.id)
        refresh_token = generate_refresh_token(user_id=user.id)
        user.set_refresh_token(refresh_token)

        return jsonify({'access_token': access_token, 'refresh_token': refresh_token})
    except Exception as e:
        return jsonify({'error': f"Server error: {e.message}"}), 500


@bp_user.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        if User.query.filter_by(username=username).first() is not None:
            return jsonify({'message': 'User already exists'}), 400

        user = User(username=username)

        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': f"Server error: {e.message}"}), 500

# @bp_user.route('/api/protected', methods=['GET'])
# @token_required
# def protected_route(current_user):
#     return jsonify({'message': f'Hello, {current_user.username}! This is a protected route.'})


@bp_user.route('/refresh', methods=['POST'])
@refresh_token_required
def refresh_token(current_user):
    try:
        access_token = generate_session_token(user_id=current_user.id)

        return jsonify({'access_token': access_token}), 201
    except Exception as e:
        return jsonify({'error': f"Server error: {e.message}"}), 500
