"""
Generate a secure secret key for production use
Run: python generate_secret_key.py
"""
import secrets

if __name__ == "__main__":
    secret_key = secrets.token_urlsafe(32)
    print("\n" + "="*60)
    print("Generated Secret Key (32+ characters):")
    print("="*60)
    print(secret_key)
    print("="*60)
    print("\nCopy this to your Railway environment variable: SECRET_KEY")
    print("="*60 + "\n")
