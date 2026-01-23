import shutil
import os
from datetime import datetime
import sys

def perform_backup():
    print("Starting backup process...")
    
    # Setup paths
    base_dir = os.getcwd()
    if 'backend' in os.listdir(base_dir):
        backend_dir = os.path.join(base_dir, 'backend')
    else:
        # We might be inside backend or elsewhere, try to find it
        if os.path.exists('GharMitra.db'):
            backend_dir = base_dir
        else:
            print("Error: Could not locate backend directory or database.")
            return

    backup_dir = os.path.join(base_dir, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # 1. Backup DB
    db_path = os.path.join(backend_dir, 'GharMitra.db')
    if os.path.exists(db_path):
        backup_db_name = f"GharMitra_FINAL_{timestamp}.db"
        backup_db_path = os.path.join(backup_dir, backup_db_name)
        try:
            shutil.copy2(db_path, backup_db_path)
            print(f"✅ Database backed up to: {backup_db_path}")
        except Exception as e:
            print(f"❌ Database backup failed: {e}")
    else:
        print(f"⚠️ Database file not found at {db_path}")

    # 2. Backup Uploads
    uploads_path = os.path.join(backend_dir, 'uploads')
    if os.path.exists(uploads_path):
        backup_uploads_name = f"uploads_{timestamp}"
        backup_uploads_path = os.path.join(backup_dir, backup_uploads_name)
        try:
            shutil.copytree(uploads_path, backup_uploads_path)
            print(f"✅ Uploads directory backed up to: {backup_uploads_path}")
        except Exception as e:
            print(f"❌ Uploads backup failed: {e}")
    else:
        print("ℹ️ No uploads directory found.")

if __name__ == "__main__":
    perform_backup()
