from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='viewer')  # 'admin' or 'viewer'
    is_admin = db.Column(db.Boolean, default=False)  # Keep for backward compatibility
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role or (role == 'admin' and self.is_admin)
    
    def is_admin_user(self):
        """Check if user is an admin"""
        return self.role == 'admin' or self.is_admin
    
    def is_viewer(self):
        """Check if user is a viewer"""
        return self.role == 'viewer'
    
    def can_edit(self):
        """Check if user can edit/create/delete"""
        return self.is_admin_user()
    
    def can_view(self):
        """Check if user can view data"""
        return True  # Both admin and viewer can view

    def __repr__(self):
        return f'<User {self.username}>'

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    website = db.Column(db.String(200))
    tier = db.Column(db.String(20), default='Silver')  # Gold, Silver, Platinum
    status = db.Column(db.String(20), default='Contacted')  # Confirmed, Contacted, Declined, Pending
    amount = db.Column(db.Float, default=0.0)
    logo_filename = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    activities = db.relationship('Activity', backref='sponsor', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('SponsorFile', backref='sponsor', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sponsor {self.name}>'

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # note, call, email, meeting
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='activities')

    def __repr__(self):
        return f'<Activity {self.activity_type}>'

class SponsorFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    original_filename = db.Column(db.String(120), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    uploader = db.relationship('User', backref='uploaded_files')

    def __repr__(self):
        return f'<SponsorFile {self.original_filename}>'
