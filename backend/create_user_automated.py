import asyncio
import sys
import os

sys.path.append(os.getcwd())

from create_admin_user import create_admin_user, list_users

async def main():
    print("Checking for existing users...")
    has_users = await list_users()
    
    if has_users:
        print("Users already exist. Skipping creation.")
        return

    print("Creating default admin user...")
    success = await create_admin_user("admin@test.com", "admin123", "Admin User")
    
    if success:
        print("Admin user created successfully.")
    else:
        print("Failed to create admin user.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
