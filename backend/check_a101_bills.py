import sqlite3

conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

print("=" * 80)
print("A-101 BILLS ANALYSIS")
print("=" * 80)

cursor.execute("""
    SELECT id, bill_number, month, year, total_amount, status, is_posted
    FROM maintenance_bills
    WHERE flat_id = 1
    ORDER BY year, month
""")
bills = cursor.fetchall()

print(f"\n{'Bill Number':<20} | {'Month/Year':<12} | {'Amount':>10} | {'Status':<6} | {'Posted':<6}")
print("-" * 80)
for bill_id, bill_num, month, year, amount, status, posted in bills:
    bill_num_str = bill_num or "NULL"
    posted_str = "Yes" if posted else "No"
    print(f"{bill_num_str:<20} | {month}/{year:<10} | {amount:>10.2f} | {status:<6} | {posted_str:<6}")

# Now show the GL transactions for A-101
print("\n" + "=" * 80)
print("A-101 TRANSACTIONS IN GL ACCOUNT 1100")
print("=" * 80)

cursor.execute("""
    SELECT date, debit_amount, credit_amount, description
    FROM transactions
    WHERE account_code = '1100'
    AND (description LIKE '%A-101%' OR description LIKE '%Flat A-101%')
    ORDER BY date
""")
txns = cursor.fetchall()

print(f"\n{'Date':<12} | {'Debit':>10} | {'Credit':>10} | Description")
print("-" * 80)
for date, debit, credit, desc in txns:
    print(f"{date:<12} | {debit:>10.2f} | {credit:>10.2f} | {desc[:60]}")

conn.close()
