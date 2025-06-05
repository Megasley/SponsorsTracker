from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User  # Lazy import to avoid circular dependency
    return User.query.get(int(user_id)) 