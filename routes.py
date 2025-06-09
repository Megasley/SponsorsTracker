import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func
from extensions import db
from models import User, Sponsor, Activity, SponsorFile
from forms import LoginForm, RegisterForm, SponsorForm, ActivityForm, FileUploadForm, ChangePasswordForm, AddUserForm
from utils import allowed_file, get_dashboard_stats
from decorators import admin_required, can_edit_required, viewer_or_admin_required
from email_utils import send_follow_up_email, send_bulk_email
from io import StringIO
import csv

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    stats = get_dashboard_stats()
    recent_sponsors = Sponsor.query.order_by(Sponsor.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', stats=stats, recent_sponsors=recent_sponsors)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/sponsors')
@login_required
def sponsors():
    search = request.args.get('search', '')
    tier_filter = request.args.get('tier', '')
    status_filter = request.args.get('status', '')
    
    query = Sponsor.query
    
    if search:
        query = query.filter(
            or_(
                Sponsor.name.contains(search),
                Sponsor.contact_person.contains(search),
                Sponsor.email.contains(search)
            )
        )
    
    if tier_filter:
        query = query.filter(Sponsor.tier == tier_filter)
    
    if status_filter:
        query = query.filter(Sponsor.status == status_filter)
    
    sponsors = query.order_by(Sponsor.created_at.desc()).all()
    
    return render_template('sponsors.html', 
                         sponsors=sponsors, 
                         search=search,
                         tier_filter=tier_filter,
                         status_filter=status_filter)

@main_bp.route('/sponsors/add', methods=['GET', 'POST'])
@can_edit_required
def add_sponsor():
    form = SponsorForm()
    if form.validate_on_submit():
        sponsor = Sponsor(
            name=form.name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            website=form.website.data,
            tier=form.tier.data,
            status=form.status.data,
            amount=form.amount.data,
            notes=form.notes.data
        )
        
        # Handle logo upload
        if form.logo.data:
            file = form.logo.data
            if allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                sponsor.logo_filename = filename
        
        db.session.add(sponsor)
        db.session.commit()
        
        # Add activity log
        activity = Activity(
            sponsor_id=sponsor.id,
            user_id=current_user.id,
            activity_type='created',
            description=f'Sponsor created by {current_user.username}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Sponsor added successfully!', 'success')
        return redirect(url_for('main.sponsor_detail', id=sponsor.id))
    
    return render_template('add_sponsor.html', form=form)

@main_bp.route('/sponsors/<int:id>')
@login_required
def sponsor_detail(id):
    sponsor = Sponsor.query.get_or_404(id)
    activities = Activity.query.filter_by(sponsor_id=id).order_by(Activity.created_at.desc()).all()
    files = SponsorFile.query.filter_by(sponsor_id=id).order_by(SponsorFile.uploaded_at.desc()).all()
    
    activity_form = ActivityForm()
    file_form = FileUploadForm()
    
    return render_template('sponsor_detail.html', 
                         sponsor=sponsor, 
                         activities=activities,
                         files=files,
                         activity_form=activity_form,
                         file_form=file_form)

@main_bp.route('/sponsors/<int:id>/edit', methods=['GET', 'POST'])
@can_edit_required
def edit_sponsor(id):
    sponsor = Sponsor.query.get_or_404(id)
    form = SponsorForm(obj=sponsor)
    
    if form.validate_on_submit():
        form.populate_obj(sponsor)
        sponsor.updated_at = datetime.utcnow()
        
        # Handle logo upload
        if form.logo.data:
            file = form.logo.data
            if allowed_file(file.filename):
                # Delete old logo if exists
                if sponsor.logo_filename:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], sponsor.logo_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                sponsor.logo_filename = filename
        
        db.session.commit()
        
        # Add activity log
        activity = Activity(
            sponsor_id=sponsor.id,
            user_id=current_user.id,
            activity_type='updated',
            description=f'Sponsor updated by {current_user.username}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Sponsor updated successfully!', 'success')
        return redirect(url_for('main.sponsor_detail', id=sponsor.id))
    
    return render_template('add_sponsor.html', form=form, sponsor=sponsor)

@main_bp.route('/sponsors/<int:id>/delete', methods=['POST'])
@can_edit_required
def delete_sponsor(id):
    sponsor = Sponsor.query.get_or_404(id)
    
    # Delete logo file if exists
    if sponsor.logo_filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], sponsor.logo_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Delete associated files
    for file in sponsor.files:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(sponsor)
    db.session.commit()
    
    flash('Sponsor deleted successfully!', 'success')
    return redirect(url_for('main.sponsors'))

@main_bp.route('/sponsors/<int:id>/activity', methods=['POST'])
@can_edit_required
def add_activity(id):
    sponsor = Sponsor.query.get_or_404(id)
    form = ActivityForm()
    
    if form.validate_on_submit():
        activity = Activity(
            sponsor_id=sponsor.id,
            user_id=current_user.id,
            activity_type=form.activity_type.data,
            description=form.description.data
        )
        db.session.add(activity)
        db.session.commit()
        flash('Activity added successfully!', 'success')
    
    return redirect(url_for('main.sponsor_detail', id=id))

@main_bp.route('/sponsors/<int:id>/upload', methods=['POST'])
@can_edit_required
def upload_file(id):
    sponsor = Sponsor.query.get_or_404(id)
    form = FileUploadForm()
    
    if form.validate_on_submit():
        file = form.file.data
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            sponsor_file = SponsorFile(
                sponsor_id=sponsor.id,
                filename=filename,
                original_filename=secure_filename(file.filename),
                file_type=file.content_type,
                file_size=os.path.getsize(file_path),
                uploaded_by=current_user.id
            )
            db.session.add(sponsor_file)
            db.session.commit()
            
            flash('File uploaded successfully!', 'success')
        else:
            flash('Invalid file type!', 'danger')
    
    return redirect(url_for('main.sponsor_detail', id=id))

@main_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main_bp.route('/settings')
@admin_required
def settings():
    users = User.query.all()
    change_password_form = ChangePasswordForm()
    add_user_form = AddUserForm()
    return render_template('settings.html', 
                         users=users,
                         change_password_form=change_password_form,
                         add_user_form=add_user_form)

@main_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
@login_required
def change_user_role(user_id):
    if not current_user.role == 'admin':
        flash('You do not have permission to change user roles.', 'error')
        return redirect(url_for('main.settings'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in ['admin', 'viewer']:
        user.role = new_role
        db.session.commit()
        flash(f'User role updated to {new_role}.', 'success')
    else:
        flash('Invalid role selected.', 'error')
    
    return redirect(url_for('main.settings'))

@main_bp.route('/export/sponsors')
@login_required
def export_sponsors():
    if not current_user.can_edit():
        flash('You do not have permission to export data.', 'error')
        return redirect(url_for('main.sponsors'))
    
    sponsors = Sponsor.query.all()
    
    # Create CSV data
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Contact Person', 'Email', 'Phone', 'Website', 'Tier', 'Status', 'Amount', 'Notes'])
    
    for sponsor in sponsors:
        writer.writerow([
            sponsor.name,
            sponsor.contact_person,
            sponsor.email,
            sponsor.phone,
            sponsor.website,
            sponsor.tier,
            sponsor.status,
            sponsor.amount,
            sponsor.notes
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=sponsors.csv'
        }
    )

@main_bp.route('/sponsors/<int:id>/send-email', methods=['POST'])
@can_edit_required
def send_sponsor_email(id):
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if not subject or not message:
        flash('Subject and message are required', 'error')
        return redirect(url_for('main.sponsor_detail', id=id))
    
    if send_follow_up_email(id, subject, message):
        flash('Email sent successfully', 'success')
    else:
        flash('Failed to send email. Please check if the sponsor has a valid email address.', 'error')
    
    return redirect(url_for('main.sponsor_detail', id=id))

@main_bp.route('/sponsors/send-bulk-email', methods=['POST'])
@can_edit_required
def send_bulk_sponsor_email():
    subject = request.form.get('subject')
    message = request.form.get('message')
    tier_filter = request.form.get('tier')
    status_filter = request.form.get('status')
    
    if not subject or not message:
        flash('Subject and message are required', 'error')
        return redirect(url_for('main.sponsors'))
    
    # Build query based on filters
    query = Sponsor.query
    if tier_filter:
        query = query.filter_by(tier=tier_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    sponsors = query.all()
    success_count = send_bulk_email(sponsors, subject, message)
    
    flash(f'Successfully sent emails to {success_count} sponsors', 'success')
    return redirect(url_for('main.sponsors'))

@main_bp.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated.', 'success')
        else:
            flash('Current password is incorrect.', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
    return redirect(url_for('main.settings'))

@main_bp.route('/settings/add-user', methods=['POST'])
@admin_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            or_(User.username == form.username.data, User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'error')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.username} has been added successfully.', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
    return redirect(url_for('main.settings'))

@main_bp.route('/settings/remove-user/<int:user_id>', methods=['POST'])
@admin_required
def remove_user(user_id):
    if user_id == current_user.id:
        flash('You cannot remove your own account.', 'error')
        return redirect(url_for('main.settings'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} has been removed.', 'success')
    return redirect(url_for('main.settings'))

# Error handlers
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
