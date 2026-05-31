#!/usr/bin/env python3
"""
Generate encryption key for Bank Statement Distribution System.
"""

from cryptography.fernet import Fernet

def generate_key():
    """Generate a new Fernet encryption key."""
    key = Fernet.generate_key()
    print("\n" + "="*60)
    print("Encryption Key Generated")
    print("="*60)
    print("\nYour encryption key:")
    print(key.decode())
    print("\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
    print("\n" + "="*60)
    print("\nIMPORTANT:")
    print("- Keep this key secure and never commit it to version control")
    print("- If you lose this key, you won't be able to decrypt stored credentials")
    print("- Use the same key across all instances of the application")
    print("="*60 + "\n")

if __name__ == '__main__':
    generate_key()
