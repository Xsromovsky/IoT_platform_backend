from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for, render_template
from flask_mail import Message
from app import mail

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_verification_token(token, expiration=600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except Exception as e:
        return False
    return email
    
def send_verification_email(user_email):
    template = generate_template(user_email=user_email)
    msg = Message(subject="Email verification", html=template, recipients=[user_email], sender=current_app.config['MAIL_USERNAME'])
    mail.send(msg)

def generate_template(user_email):
    token = generate_verification_token(user_email)
    link = url_for('user_routes.verify_email_token', token=token, _external=True)
    html = render_template('email_verification.html', verify_url=link)
    return html