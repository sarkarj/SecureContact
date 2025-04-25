import secrets

# Generate a random 24-byte (192-bit) secret key
secret_key = secrets.token_hex(24)

print(f"Generated Secret Key: {secret_key}")
