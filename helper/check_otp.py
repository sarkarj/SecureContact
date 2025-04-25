import os
import pyotp
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

TOTP_SECRET = os.getenv("TOTP_SECRET")
if not TOTP_SECRET:
    print("TOTP_SECRET not loaded!")
else:
    totp = pyotp.TOTP(TOTP_SECRET)
    print(f"Generated OTP: {totp.now()}")