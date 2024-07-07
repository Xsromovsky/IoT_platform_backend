from flask_mail import  Message
from app import mail



def send_mail_to(recipient, body, subject, sender):
    msg = Message(subject=subject, body=body, recipients=[recipient], sender=sender)
    mail.send(msg)
    