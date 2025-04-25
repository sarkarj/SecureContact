import os
import pyotp
import qrcode
from dotenv import load_dotenv

load_dotenv()

# Try loading secret from .env
secret = os.getenv("TOTP_SECRET")

# If not found, generate one
if not secret:
    secret = pyotp.random_base32()
    print(f"🔐 Generated new secret: {secret}")
    print("⚠️  Please add this to your .env file as:")
    print(f"TOTP_SECRET={secret}")

# Always save secret to file (even if it was loaded from .env)
with open("totp_secret.txt", "w") as f:
    f.write(f"TOTP_SECRET={secret}\n")
print("📝 Secret saved to 'totp_secret.txt'.")

# Generate provisioning URI
totp_uri = pyotp.TOTP(secret).provisioning_uri(name="Client Connect", issuer_name="JSarkar")

# Generate and save QR code
qr = qrcode.make(totp_uri)
qr.save("totp_qr.png")
print("✅ Scan 'totp_qr.png' using Microsoft/Google Authenticator.")