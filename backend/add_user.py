"""
Script to add new users (committee members/residents) to GharMitra
"""
import requests
import json
import sys

# Fix encoding for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Backend URL
BASE_URL = "http://localhost:8001/api"

def add_user(name, email, password, flat_number, role="resident"):
    """
    Add a new user to the system

    Args:
        name: Full name of the user
        email: Email address (will be used for login)
        password: Login password
        flat_number: Flat number (e.g., "A-101", "A-202")
        role: User role - "admin", "resident", "treasurer", "secretary", "auditor"
    """
    url = f"{BASE_URL}/auth/register"

    data = {
        "name": name,
        "email": email,
        "password": password,
        "apartment_number": flat_number,
        "role": role,
        "phone_number": "",  # Optional
        "terms_accepted": True,
        "privacy_accepted": True,
        "consent_version": "1.0"
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"✓ User created successfully!")
        print(f"  Name: {name}")
        print(f"  Email: {email}")
        print(f"  Flat: {flat_number}")
        print(f"  Role: {role}")
        print(f"  User ID: {result.get('user', {}).get('id', 'N/A')}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"✗ Failed to create user: {e.response.json().get('detail', str(e))}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

# Example usage - Add committee members
if __name__ == "__main__":
    print("=" * 80)
    print("GharMitra - Add Users Script")
    print("=" * 80)
    print()

    # Example 1: Add Treasurer
    print("1. Adding Treasurer...")
    add_user(
        name="Rajesh Kumar",
        email="rajesh.treasurer@example.com",
        password="password123",
        flat_number="A-101",
        role="treasurer"
    )
    print()

    # Example 2: Add Secretary
    print("2. Adding Secretary...")
    add_user(
        name="Priya Sharma",
        email="priya.secretary@example.com",
        password="password123",
        flat_number="A-201",
        role="secretary"
    )
    print()

    # Example 3: Add Regular Resident
    print("3. Adding Resident...")
    add_user(
        name="Amit Singh",
        email="amit.resident@example.com",
        password="password123",
        flat_number="A-301",
        role="resident"
    )
    print()

    print("=" * 80)
    print("Done! You can now:")
    print("1. Log in with these credentials")
    print("2. Change their roles from Settings → Roles & Permissions")
    print("=" * 80)

    # Interactive mode - add your own users
    print()
    print("Would you like to add more users interactively? (yes/no): ", end="")
    response = input().strip().lower()

    if response == "yes":
        while True:
            print()
            print("Enter user details (or press Enter for name to quit):")
            name = input("Name: ").strip()
            if not name:
                break

            email = input("Email: ").strip()
            password = input("Password: ").strip()
            flat_number = input("Flat Number (e.g., A-101): ").strip()

            print("Role options: admin, treasurer, secretary, auditor, resident")
            role = input("Role (default: resident): ").strip() or "resident"

            add_user(name, email, password, flat_number, role)

            print()
            print("Add another user? (yes/no): ", end="")
            if input().strip().lower() != "yes":
                break

    print()
    print("All done!")
