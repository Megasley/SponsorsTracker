from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Confirm Password', 
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')]
    )

class SponsorForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    website = StringField('Website', validators=[Optional(), Length(max=200)])
    tier = SelectField('Tier', choices=[
        ('Silver', 'Silver'),
        ('Gold', 'Gold'),
        ('Platinum', 'Platinum')
    ], default='Silver')
    status = SelectField('Status', choices=[
        ('Contacted', 'Contacted'),
        ('Confirmed', 'Confirmed'),
        ('Declined', 'Declined'),
        ('Pending', 'Pending')
    ], default='Contacted')
    amount = FloatField('Sponsorship Amount', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Notes', validators=[Optional()])
    logo = FileField('Logo', validators=[
        Optional(),
        FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only!')
    ])

class ActivityForm(FlaskForm):
    activity_type = SelectField('Activity Type', choices=[
        ('note', 'Note'),
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('follow_up', 'Follow-up')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])

class FileUploadForm(FlaskForm):
    file = FileField('File', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'png', 'gif'], 'Invalid file type!')
    ])
