from flask import current_app, render_template
from flask_mail import Mail, Message
from models import Sponsor
from extensions import db

mail = Mail()

def send_email(to, subject, template, **kwargs):
    """Send an email using a template"""
    msg = Message(
        subject,
        recipients=[to],
        html=render_template(f'emails/{template}.html', **kwargs)
    )
    mail.send(msg)

def send_follow_up_email(sponsor_id, subject, message):
    """Send a follow-up email to a sponsor"""
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    if not sponsor.email:
        return False
    
    send_email(
        to=sponsor.email,
        subject=subject,
        template='follow_up',
        sponsor=sponsor,
        message=message
    )
    return True

def send_bulk_email(sponsors, subject, message):
    """Send an email to multiple sponsors"""
    success_count = 0
    for sponsor in sponsors:
        if sponsor.email:
            try:
                send_email(
                    to=sponsor.email,
                    subject=subject,
                    template='bulk_email',
                    sponsor=sponsor,
                    message=message
                )
                success_count += 1
            except Exception as e:
                current_app.logger.error(f"Failed to send email to {sponsor.email}: {str(e)}")
    
    return success_count 