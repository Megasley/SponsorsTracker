from flask_login import current_user
from sqlalchemy import func
from models import Sponsor, Activity

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_dashboard_stats():
    """Get dashboard statistics"""
    total_sponsors = Sponsor.query.count()
    total_raised = Sponsor.query.with_entities(func.sum(Sponsor.amount)).scalar() or 0
    confirmed_sponsors = Sponsor.query.filter_by(status='Confirmed').count()
    
    # Get upcoming follow-ups (activities created in last 7 days that need follow-up)
    upcoming_followups = Activity.query.filter_by(activity_type='follow_up').count()
    
    return {
        'total_sponsors': total_sponsors,
        'total_raised': total_raised,
        'confirmed_sponsors': confirmed_sponsors,
        'upcoming_followups': upcoming_followups
    }

def get_status_badge_class(status):
    """Get Bootstrap badge class for sponsor status"""
    status_classes = {
        'Confirmed': 'success',
        'Declined': 'danger',
        'Pending': 'warning',
        'Contacted': 'info'
    }
    return status_classes.get(status, 'secondary')

def get_tier_badge_class(tier):
    """Get Bootstrap badge class for sponsor tier"""
    tier_classes = {
        'Platinum': 'light',
        'Gold': 'warning',
        'Silver': 'secondary'
    }
    return tier_classes.get(tier, 'secondary')

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"
