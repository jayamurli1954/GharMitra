import sqlite3
import os
import shutil

def recover_database(corrupted_path, current_path):
    print(f"\n--- Robust Database Recovery Started ---")
    print(f"Source: {corrupted_path}")
    print(f"Target: {current_path}")
    
    if not os.path.exists(corrupted_path):
        print(f"❌ Source file not found: {corrupted_path}")
        return

    try:
        # Try URI connection which sometimes allows reading even if header is slightly off
        source_uri = f"file:{corrupted_path}?mode=ro&immutable=1"
        source_conn = sqlite3.connect(source_uri, uri=True)
        source_cursor = source_conn.cursor()
        
        # Get list of tables
        try:
            source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in source_cursor.fetchall() if not t[0].startswith('sqlite_')]
        except Exception:
            print("⚠️  sqlite_master corrupted. Using hardcoded table list.")
            tables = ["users", "societies", "account_codes", "flats", "members", "maintenance_bills", "transactions", "journal_entries", "assets"]
        
        print(f"Processing {len(tables)} tables...")

        # Re-initialize clean target
        if os.path.exists(current_path):
            shutil.copy2(current_path, current_path + ".pre_robust")
            # We don't remove it, we'll try to insert into existing schema if possible,
            # but it's cleaner to start with a schema-only DB.
            # However, init_db() already ran and created schema.
        
        target_conn = sqlite3.connect(current_path)
        target_cursor = target_conn.cursor()
        
        # Disable foreign keys for recovery
        target_cursor.execute("PRAGMA foreign_keys = OFF")

        for table in tables:
            print(f"Processing table: {table}...", end="", flush=True)
            try:
                source_cursor.execute(f"SELECT * FROM {table}")
                rows = []
                success_count = 0
                error_count = 0
                
                while True:
                    try:
                        row = source_cursor.fetchone()
                        if row is None: break
                        rows.append(row)
                        success_count += 1
                    except Exception:
                        error_count += 1
                        continue # Skip corrupted row
                
                if rows:
                    placeholders = ",".join(["?"] * len(rows[0]))
                    target_cursor.executemany(f"INSERT OR REPLACE INTO {table} VALUES ({placeholders})", rows)
                    target_conn.commit()
                print(f" Done. (Recovered: {success_count}, Failed: {error_count})")
                
            except Exception as e:
                print(f" ❌ Table access failed: {e}")

        target_conn.close()
        source_conn.close()
        print(f"\n✨ Robust Recovery finished.")
        
    except Exception as e:
        print(f"❌ Recovery failed: {e}")

if __name__ == "__main__":
    CORRUPTED = "gharmitra_corrupted.db"
    CURRENT = "gharmitra.db"
    recover_database(CORRUPTED, CURRENT)
