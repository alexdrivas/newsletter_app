from flask_mail import Message
from app import mail

def send_email(to, subject, body):
    try:
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)
