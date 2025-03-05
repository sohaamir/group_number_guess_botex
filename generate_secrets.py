import secrets
import string

def generate_secure_password(length=16):
    """Generate a secure random password of specified length"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def generate_secret_key(length=50):
    """Generate a secure random secret key of specified length"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return secret_key

# Generate and print values
admin_password = generate_secure_password(16)
secret_key = generate_secret_key(50)

print(f"OTREE_ADMIN_PASSWORD={admin_password}")
print(f"OTREE_SECRET_KEY={secret_key}")
print("\nAdd these to your .env file or Heroku config vars.")