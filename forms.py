# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class OTPForm(FlaskForm):
    otp = StringField('Enter OTP', validators=[DataRequired()])
    submit = SubmitField('Verify OTP')