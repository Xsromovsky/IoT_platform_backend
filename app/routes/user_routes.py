from flask import Blueprint, request, jsonify, current_app
# from werkzeug.security import generate_password_hash, check_password_hash
from app import db, mail
from app.models import User, BlacklistToken
from app.auth import token_required, refresh_token_required
# from app.utils.dev_token_generator import generate_api_token
from app.utils.user_token_generator import generate_refresh_token, generate_session_token
from flask_mail import Message
from app.utils.email_verification import send_verification_email, confirm_verification_token

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
    email = data.get('email')
    try:
        if User.query.filter_by(username=username, email=email).first() is not None:
            return jsonify({'message': 'User already exists'}), 400
        if User.query.filter_by(email=email).first() is not None:
            return jsonify({'message': 'Email already exists'}), 400
            
        if User.validate_email(email):
            try:
                user = User(username=username, email=email)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                send_verification_email(email)
                return jsonify({'message': 'User registered successfully\n A verification email has been sent to your email address'}), 201
            except Exception:
                db.session.rollback()
                return jsonify({'message': 'User registration failed'}), 400
        else:
            return jsonify({'Message': 'Email is invalid'}), 401
    except Exception as e:
        return jsonify({'error': f"Server error!!: {e}"}), 500

@bp_user.route('/refresh', methods=['POST'])
@refresh_token_required
def refresh_token(current_user):
    try:
        access_token = generate_session_token(user_id=current_user.id)

        return jsonify({'access_token': access_token}), 201
    except Exception as e:
        return jsonify({'error': f"Server error: {e.message}"}), 500



@bp_user.route('/user/data', methods=['GET'])
@token_required
def get_user_data(current_user):
    user_data = User.query.filter_by(id=current_user.id, username=current_user.username).first_or_404()
    return jsonify({'user_data': user_data.to_dict()}), 200

@bp_user.route('/user/verify_token', methods=['GET'])
def verify_email_token():
    token = request.args.get('token')
    verified_email = confirm_verification_token(token)
    try:
        user = User.query.filter_by(email=verified_email).first_or_404()
        user.email_verified = True
        db.session.add(user)
        db.session.commit()

        return jsonify({'email is verified': verified_email}), 201
    except Exception as e:
        return jsonify({'Error': e}), 500


@bp_user.route('/logout', methods=['GET'])
@token_required
def logout(current_user):
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header
        try:
            blacklist_token = BlacklistToken(token=token)
            db.session.add(blacklist_token)
            
            current_user.refresh_token = None
            
            db.session.commit()
            
            return jsonify({'message': 'Successfully logged out.'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Error logging out, please try again.'}), 500
    else:
        return jsonify({'message': 'Token is missing!'}), 403