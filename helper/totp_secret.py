import pyotp
# Generate a random base32 secret key
secret = pyotp.random_base32()
print("TOTP_SECRET =", secret)