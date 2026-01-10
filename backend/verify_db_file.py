from app.config import settings
import os

print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"Current Working Directory: {os.getcwd()}")
if "sqlite" in settings.DATABASE_URL:
    db_file_name = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("./", "")
    abs_path = os.path.abspath(db_file_name)
    print(f"Absolute Database Path: {abs_path}")
    if os.path.exists(abs_path):
        print("Database file exists on disk.")
    else:
        print("Database file does NOT exist on disk.")
