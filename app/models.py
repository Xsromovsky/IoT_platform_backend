from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from email_validator import validate_email, EmailNotValidError
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    refresh_token = db.Column(db.String(512), nullable=True)
    email = db.Column(db.String(256), nullable=False, unique=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)

    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password_hash(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_refresh_token(self, token):
        self.refresh_token = token
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'email_verified': self.email_verified
        }
        
    @staticmethod
    def validate_email(email):
        try:
            valid_email = validate_email(email)
            return True
        except EmailNotValidError as e:
            return False

class Device(db.Model):
    dev_id = db.Column(db.Integer, primary_key=True)
    dev_name = db.Column(db.String(50), nullable=False)
    dev_type = db.Column(db.String(50), nullable=False)
    dev_token = db.Column(db.String(64), nullable=False)
    dev_measurement = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class BlacklistToken(db.Model):
    __tablename__ = 'blacklist_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(512), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.now()

    @staticmethod
    def check_blacklist(auth_token):
        res = BlacklistToken.query.filter_by(token=auth_token).first()
        return bool(res)