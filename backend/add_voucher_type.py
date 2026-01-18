import sqlite3
from datetime import date

# Connect to the database
conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

# Fix: Mark December 2025 bill for A-101 (flat_id=1) as PAID
print("Fixing A-101 December 2025 bill status...")
cursor.execute("""
    UPDATE maintenance_bills
    SET status = 'PAID', paid_date = '2026-01-10'
    WHERE flat_id = 1 AND month = 12 AND year = 2025 AND status = 'UNPAID'
""")

rows_updated = cursor.rowcount
conn.commit()

if rows_updated > 0:
    print(f"SUCCESS: Updated {rows_updated} bill(s) for A-101 to PAID status")
else:
    print("INFO: No bills found to update")

# Verify the update
cursor.execute("""
    SELECT month, year, total_amount, status, paid_date
    FROM maintenance_bills
    WHERE flat_id = 1
    ORDER BY year DESC, month DESC
""")
bills = cursor.fetchall()
print("\nMaintenance Bills for A-101 after update:")
for bill in bills:
    print(f"  {bill[0]}/{bill[1]}: Rs {bill[2]} - {bill[3]} (Paid: {bill[4] or 'N/A'})")

conn.close()
