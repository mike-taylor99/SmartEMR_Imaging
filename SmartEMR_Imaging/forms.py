from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from SmartEMR_Imaging.model import User


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.objects(email=email.data).first()
        if user:
            raise ValidationError('The email is already registered with an account!')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.objects(email=email.data).first()
            if user:
                raise ValidationError('The email is already registered with an account!')

class UploadMedicalImage(FlaskForm):
    pid = StringField('Patient ID', validators=[DataRequired(), Length(min=2, max=20)])
    tags = StringField('Tags (separate by commas)', validators=[DataRequired(), Length(min=2)])
    date = DateTimeField('Image Time and Date (Y-m-d H:M:S)', validators=[DataRequired()])
    image = FileField('Upload Medical Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], DataRequired())])
    submit1 = SubmitField('Upload')

class PatientImages(FlaskForm):
    pid = StringField('Patient ID', validators=[DataRequired(), Length(min=2, max=20)])
    submit2 = SubmitField('Submit')

class RegularImgQuery(FlaskForm):
    pid = StringField('Patient ID')
    tags = StringField('Tags (separate by commas)')
    submit3 = SubmitField('Submit')

class NLImgQuery(FlaskForm):
    query = StringField('Natural Language Query', validators=[DataRequired(), Length(min=2)])
    submit4 = SubmitField('Submit')

class Classify(FlaskForm):
    image = FileField('Upload Medical Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], DataRequired())])
    submit5 = SubmitField('Classify')