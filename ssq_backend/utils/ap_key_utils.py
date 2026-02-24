import secrets
import hashlib


def generate_api_key():
    raw = secrets.token_hex(32)
    return hashlib.sha256(raw.encode()).hexdigest()