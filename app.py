from flask import Flask, render_template, request, session, Response, jsonify, redirect, url_for
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.csrf import CSRFError
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cryptography.fernet import Fernet, InvalidToken
from captcha.image import ImageCaptcha
from decouple import config
from datetime import datetime, timedelta
from dateutil import parser
from forms import OTPForm
import sqlite3
import random
import string
import hashlib
import logging
import requests
import pyotp

# Flask app setup
app = Flask(__name__)
app.secret_key = config('SECRET_KEY')
app.config.update(
    WTF_CSRF_ENABLED=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=config('FLASK_ENV', default='development') == 'production',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=5)
)

csrf = CSRFProtect(app)
limiter = Limiter(key_func=get_remote_address, default_limits=["10 per minute"])
#limiter.init_app(app)
limiter = Limiter(app, storage_uri=config('RATELIMIT_STORAGE_URL'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NUMVERIFY_API_KEY = config('NUMVERIFY_API_KEY')
FERNET_KEY = config('FERNET_KEY')
fernet = Fernet(FERNET_KEY)
DB_NAME = config('DB_NAME', default='database.db')
TOTP_SECRET = config('TOTP_SECRET')

# Database helper
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# WTForms form
class UserForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(max=50),
        Regexp(r'^[a-zA-Z.\s]+$', message='Name must contain only letters, spaces, and dots.')
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=50)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    prefer_time = SelectField('Preferred Time', choices=[('Morning', 'Morning'), ('Evening', 'Evening')])
    captcha = StringField('Captcha', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/')
def index():
    form = UserForm()
    return render_template('index.html', form=form)

@app.route('/submit', methods=['POST'])
@limiter.limit("5 per second")
def submit():
    form = UserForm()
    if not form.validate_on_submit():
        return jsonify({"status": "error", "message": "Invalid form fields."})

    name = form.name.data
    email = form.email.data
    phone = ''.join(filter(str.isdigit, form.phone.data))
    prefer_time = form.prefer_time.data
    entered_captcha = form.captcha.data
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not validate_captcha(entered_captcha):
        return jsonify({"status": "captcha_fail"})

    validation_result = validate_phone_number(phone)
    if not validation_result.get('valid'):
        return jsonify({"status": "invalid_phone"})

    email_phone_hash = generate_email_phone_hash(email, phone)

    if email_phone_combination_exists(email_phone_hash):
        return jsonify({"status": "exists"})

    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO users (name, email, phone, email_phone_hash, prefer_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (encrypt_data(name), encrypt_data(email), encrypt_data(phone), email_phone_hash, prefer_time, timestamp))
        conn.commit()

    session['submitted'] = True
    return jsonify({"status": "success"})

@app.route('/captcha')
def generate_captcha():
    captcha = ImageCaptcha(width=200, height=100)
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    session['captcha_text'] = hashlib.sha256(captcha_text.encode()).hexdigest()
    image_data = captcha.generate(captcha_text)
    response = Response(image_data, content_type='image/png')
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/otp_verify', methods=['GET', 'POST'])
def otp_verify():
    form = OTPForm()
    if request.method == 'POST':
        otp_input = form.otp.data  # safer than request.form.get('otp')
        if verify_otp(otp_input):
            session['otp_verified'] = True
            return redirect(url_for('display'))
        else:
            return render_template('otp_verify.html', form=form, error='Invalid OTP. Please try again.')
    return render_template('otp_verify.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/display_data')
def display():
    if not session.get('otp_verified'):
        return redirect(url_for('otp_verify'))

    with get_db_connection() as conn:
        data = conn.execute('SELECT id, name, email, phone, prefer_time, timestamp, contact_timestamp, response FROM users ORDER BY timestamp DESC').fetchall()

    decrypted_data = [
        (
            row["id"],
            decrypt_data(row["name"]),
            decrypt_data(row["email"]),
            decrypt_data(row["phone"]),
            row["prefer_time"],
            row["timestamp"],
            row["contact_timestamp"],
            decrypt_data(row["response"]) if row["response"] else None
        ) for row in data
    ]
    form = UserForm()
    return render_template('display_data.html', data=decrypted_data, form=form)

@app.route('/update_record', methods=['POST'])
def update_record():
    data = request.get_json()
    record_id = data.get('id')
    response = data.get('response')

    if not record_id or not response:
        return jsonify({"status": "error", "message": "Missing required fields."})

    encrypted_response = encrypt_data(response)
    contact_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        with get_db_connection() as conn:
            conn.execute('''
                UPDATE users
                SET response = ?, contact_timestamp = ?
                WHERE id = ?
            ''', (encrypted_response, contact_timestamp, record_id))
            conn.commit()

        return jsonify({
            "status": "success",
            "contact_timestamp": contact_timestamp
        })
    except Exception as e:
        logger.error(f"Error updating record: {e}")
        return jsonify({"status": "error", "message": "Database update failed."})

@app.route('/healthz')
def health_check():
    return "OK", 200

# Helpers
def validate_captcha(entered_captcha):
    stored_hash = session.get('captcha_text', '')
    return hashlib.sha256(entered_captcha.encode()).hexdigest() == stored_hash

def validate_phone_number(phone_number):
    url = f'http://apilayer.net/api/validate?access_key={NUMVERIFY_API_KEY}&number={phone_number}&country_code=US&format=1'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error("Numverify API call failed: %s", e)
    return {'valid': False, 'error': 'Phone verification failed'}

def email_phone_combination_exists(email_phone_hash):
    with get_db_connection() as conn:
        return conn.execute('SELECT 1 FROM users WHERE email_phone_hash = ?', (email_phone_hash,)).fetchone() is not None

def encrypt_data(data):
    return fernet.encrypt(data.encode())

def decrypt_data(data):
    try:
        return fernet.decrypt(data.encode() if isinstance(data, str) else data).decode()
    except InvalidToken:
        logger.error("Invalid encryption token encountered during decryption")
        return "[DECRYPTION ERROR]"
    except Exception as e:
        logger.error("Decryption error: %s", e)
        return "[ERROR]"

def generate_email_phone_hash(email, phone):
    return hashlib.sha256(f"{email}{phone}".encode()).hexdigest()

def verify_otp(otp):
    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.verify(otp)

@app.template_filter('pretty_datetime')
def pretty_datetime(value):
    if not value:
        return '—'
    try:
        if isinstance(value, str):
            dt = parser.parse(value)
        elif isinstance(value, datetime):
            dt = value
        else:
            return str(value)
        return dt.strftime('%b %d, %Y %I:%M %p')
    except Exception as e:
        logger.warning(f"Could not parse date: {value} — {e}")
        return str(value)
app.jinja_env.filters['pretty_datetime'] = pretty_datetime

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    logger.error(f"CSRF error: {e.description}")
    return render_template('csrf_error.html', reason=e.description), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
