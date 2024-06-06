from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    refresh_token = db.Column(db.String(256))

    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password_hash(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_refresh_token(self, token):
        self.refresh_token = token
        db.session.commit()

class Device(db.Model):
    dev_id = db.Column(db.Integer, primary_key=True)
    dev_name = db.Column(db.String(50), nullable=False)
    dev_type = db.Column(db.String(50))
    dev_token = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    