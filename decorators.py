from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user, login_required

def admin_required(f):
    """Decorator to require admin role for a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin_user():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def can_edit_required(f):
    """Decorator to require edit permissions (admin only)"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.can_edit():
            flash('Access denied. You do not have permission to modify data.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def viewer_or_admin_required(f):
    """Decorator to require viewer or admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.can_view():
            flash('Access denied.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function