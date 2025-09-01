#!/usr/bin/env python3
"""
Generate a new Django secret key for production use.
Run this script to generate a secure secret key for your .env file.
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("Generated SECRET_KEY:")
    print(secret_key)
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
