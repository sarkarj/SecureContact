from cryptography.fernet import Fernet
# Generate a Fernet key
key = Fernet.generate_key()
# Print the generated key
print(key.decode('utf-8'))

