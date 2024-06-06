import secrets
import string

def generate_api_token(length=48):
    characters = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(characters)for _ in range(length))
    return token
