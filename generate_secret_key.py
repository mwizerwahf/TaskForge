"""
Generate a secure SECRET_KEY for production deployment
Run: python generate_secret_key.py
"""
import secrets

secret_key = secrets.token_hex(32)
print("\n" + "="*60)
print("Generated SECRET_KEY for production:")
print("="*60)
print(f"\n{secret_key}\n")
print("Add this to your .env file:")
print(f"SECRET_KEY={secret_key}")
print("\nOr update docker-compose.yml:")
print(f"  SECRET_KEY: {secret_key}")
print("="*60 + "\n")
