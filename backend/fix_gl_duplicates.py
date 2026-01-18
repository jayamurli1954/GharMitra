import sqlite3
from decimal import Decimal

conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

print("=" * 80)
print("IDENTIFYING DUPLICATE GL TRANSACTIONS FOR A-101")
print("=" * 80)

# Find all A-101 transactions
cursor.execute("""
    SELECT id, date, debit_amount, credit_amount, description
    FROM transactions
    WHERE account_code = '1100'
    AND (description LIKE '%A-101%' OR description LIKE '%Flat A-101%')
    ORDER BY date, id
""")
transactions = cursor.fetchall()

print(f"\n{'ID':<6} | {'Date':<12} | {'Debit':>10} | {'Credit':>10} | Description")
print("-" * 100)
for txn_id, date, debit, credit, desc in transactions:
    print(f"{txn_id:<6} | {date:<12} | {debit:>10.2f} | {credit:>10.2f} | {desc[:60]}")

print("\n" + "=" * 80)
print("TRANSACTIONS TO DELETE (Duplicates/Errors)")
print("=" * 80)

# Identify transactions to delete
to_delete = []

# 1. Delete the Rs 1,235 debit (first regeneration - wrong amount)
cursor.execute("""
    SELECT id FROM transactions
    WHERE account_code = '1100'
    AND debit_amount = 1235
    AND description LIKE '%Regenerated Bill BILL-2025-12-020 for Flat A-101%'
    AND description LIKE '%regenerated with 3 occupants%'
""")
result = cursor.fetchone()
if result:
    to_delete.append(('Debit Rs 1,235 - First regeneration (wrong)', result[0]))

# 2. Delete ONE of the Rs 3,135 debits (second regeneration - duplicate)
# Keep the "Maintenance charges" one, delete the "Regenerated Bill" one
cursor.execute("""
    SELECT id FROM transactions
    WHERE account_code = '1100'
    AND debit_amount = 3135
    AND description LIKE '%Regenerated Bill BILL-2025-12-020 for Flat A-101%'
    AND description LIKE '%now corrected with all components%'
""")
result = cursor.fetchone()
if result:
    to_delete.append(('Debit Rs 3,135 - Second regeneration (duplicate)', result[0]))

# 3. Delete the Rs 3,546.34 reversal (reversing non-existent bill)
cursor.execute("""
    SELECT id FROM transactions
    WHERE account_code = '1100'
    AND credit_amount = 3546.34
    AND description LIKE '%Reversal: Bill None for Flat A-101%'
""")
result = cursor.fetchone()
if result:
    to_delete.append(('Credit Rs 3,546.34 - Reversal of non-existent bill', result[0]))

# 4. Delete the Rs 1,235 reversal (since we're deleting the original debit)
cursor.execute("""
    SELECT id FROM transactions
    WHERE account_code = '1100'
    AND credit_amount = 1235
    AND description LIKE '%Reversal: Bill BILL-2025-12-020 for Flat A-101%'
    AND description LIKE '%wrongly calculated%'
""")
result = cursor.fetchone()
if result:
    to_delete.append(('Credit Rs 1,235 - Reversal (matching the debit we deleted)', result[0]))

print(f"\nFound {len(to_delete)} transactions to delete:")
for desc, txn_id in to_delete:
    print(f"  ID {txn_id}: {desc}")

if to_delete:
    print("\n" + "=" * 80)
    print("DELETING DUPLICATE TRANSACTIONS")
    print("=" * 80)
    
    for desc, txn_id in to_delete:
        cursor.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        print(f"  Deleted transaction ID {txn_id}: {desc}")
    
    conn.commit()
    print(f"\nSuccessfully deleted {len(to_delete)} duplicate transactions")
else:
    print("\nNo transactions to delete")

# Recalculate and update Account 1100 balance
print("\n" + "=" * 80)
print("RECALCULATING ACCOUNT 1100 BALANCE")
print("=" * 80)

cursor.execute("""
    SELECT
        SUM(debit_amount) as total_debits,
        SUM(credit_amount) as total_credits
    FROM transactions
    WHERE account_code = '1100'
""")
debits, credits = cursor.fetchone()
new_balance = Decimal(str(debits or 0)) - Decimal(str(credits or 0))

cursor.execute("""
    UPDATE account_codes
    SET current_balance = ?
    WHERE code = '1100'
""")
cursor.execute("UPDATE account_codes SET current_balance = ? WHERE code = '1100'", (float(new_balance),))
conn.commit()

print(f"Total Debits: Rs {Decimal(str(debits or 0)):,.2f}")
print(f"Total Credits: Rs {Decimal(str(credits or 0)):,.2f}")
print(f"New Balance: Rs {new_balance:,.2f}")

# Verify against expected
cursor.execute("""
    SELECT SUM(total_amount)
    FROM maintenance_bills
    WHERE status = 'UNPAID' AND is_posted = 1
""")
expected = Decimal(str(cursor.fetchone()[0] or 0))

print(f"\nExpected Balance (Unpaid Posted Bills): Rs {expected:,.2f}")
print(f"Difference: Rs {abs(new_balance - expected):,.2f}")

if abs(new_balance - expected) < Decimal('0.01'):
    print("\n✓ SUCCESS: GL Balance now matches expected!")
else:
    print(f"\n✗ WARNING: Still have a difference of Rs {abs(new_balance - expected):,.2f}")

conn.close()
print("\n" + "=" * 80)
