"""
Add flat_id column to transactions table

This migration adds a flat_id foreign key to the transactions table
to properly track which flat each transaction belongs to, instead of
relying on parsing transaction descriptions.
"""

import sqlite3

conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

print("=" * 80)
print("ADDING flat_id COLUMN TO transactions TABLE")
print("=" * 80)

# Check if column already exists
cursor.execute("PRAGMA table_info(transactions)")
columns = [col[1] for col in cursor.fetchall()]

if 'flat_id' in columns:
    print("\nflat_id column already exists. Skipping migration.")
else:
    print("\nAdding flat_id column...")

    # Add the column
    cursor.execute("""
        ALTER TABLE transactions
        ADD COLUMN flat_id INTEGER REFERENCES flats(id)
    """)

    # Create index for better query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_flat_id
        ON transactions(flat_id)
    """)

    conn.commit()
    print("SUCCESS: flat_id column added successfully")
    print("SUCCESS: Index created on flat_id")

# Now update existing transactions by parsing their descriptions
print("\n" + "=" * 80)
print("UPDATING EXISTING TRANSACTIONS WITH FLAT_ID")
print("=" * 80)

# Get all flats
cursor.execute("SELECT id, flat_number FROM flats ORDER BY flat_number")
flats = cursor.fetchall()

print(f"\nFound {len(flats)} flats")

updated_count = 0

for flat_id, flat_number in flats:
    # Update transactions that mention this flat in their description
    # Looking for patterns like:
    # - "Flat: A-101"
    # - "Flat A-101"
    # - "for A-101"
    # - "from A-101"

    cursor.execute("""
        UPDATE transactions
        SET flat_id = ?
        WHERE flat_id IS NULL
        AND (
            description LIKE ?
            OR description LIKE ?
            OR description LIKE ?
            OR description LIKE ?
        )
    """, (flat_id,
          f'%Flat: {flat_number}%',
          f'%Flat {flat_number}%',
          f'%for {flat_number}%',
          f'%from {flat_number}%'))

    rows_updated = cursor.rowcount
    if rows_updated > 0:
        updated_count += rows_updated
        print(f"  {flat_number}: Updated {rows_updated} transaction(s)")

conn.commit()

print(f"\nSUCCESS: Total transactions updated: {updated_count}")

# Verify the results
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

cursor.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(flat_id) as with_flat_id,
        COUNT(*) - COUNT(flat_id) as without_flat_id
    FROM transactions
""")

total, with_flat, without_flat = cursor.fetchone()

print(f"\nTotal transactions: {total}")
print(f"Transactions with flat_id: {with_flat}")
print(f"Transactions without flat_id: {without_flat}")

# Show Account 1100 transactions
cursor.execute("""
    SELECT
        COUNT(*) as total_1100,
        COUNT(flat_id) as with_flat_id
    FROM transactions
    WHERE account_code = '1100'
""")

total_1100, with_flat_1100 = cursor.fetchone()

print(f"\nAccount 1100 (Maintenance Dues) transactions: {total_1100}")
print(f"Account 1100 with flat_id: {with_flat_1100}")

if with_flat_1100 < total_1100:
    print(f"\nWARNING: {total_1100 - with_flat_1100} Account 1100 transactions still missing flat_id")
    print("These may need manual assignment.")

conn.close()

print("\n" + "=" * 80)
print("MIGRATION COMPLETED")
print("=" * 80)
