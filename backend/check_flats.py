import sqlite3
import os

DB_PATH = "gharmitra.db"

def check_flats():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Checking Flats in {DB_PATH}...")
    
    cursor.execute("SELECT id, flat_number, block, floor FROM flats")
    flats = cursor.fetchall()
    
    if not flats:
        print("No flats found in the database.")
    else:
        print(f"Found {len(flats)} flats:")
        for flat in flats:
            print(f"- ID: {flat[0]}, Number: {flat[1]}, Block: {flat[2]}, Floor: {flat[3]}")

    conn.close()

if __name__ == "__main__":
    check_flats()
