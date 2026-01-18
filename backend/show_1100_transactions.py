import sqlite3
from decimal import Decimal

conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

print("=" * 120)
print("ALL TRANSACTIONS FOR ACCOUNT 1100 - MAINTENANCE DUES RECEIVABLE")
print("=" * 120)

cursor.execute("""
    SELECT date, debit_amount, credit_amount, description
    FROM transactions
    WHERE account_code = '1100'
    ORDER BY date, id
""")
txns = cursor.fetchall()

print(f"\n{'Date':<12} | {'Debit':>10} | {'Credit':>10} | {'Balance':>10} | Description")
print("-" * 120)

running = Decimal(0)
for date, debit, credit, desc in txns:
    debit = Decimal(str(debit))
    credit = Decimal(str(credit))
    running += debit - credit
    desc_short = desc[:70] if len(desc) <= 70 else desc[:67] + "..."
    print(f"{date:<12} | {debit:>10.2f} | {credit:>10.2f} | {running:>10.2f} | {desc_short}")

print("\n" + "=" * 120)
print(f"Final GL Balance: Rs {running:,.2f}")

# Now check the account_codes table
cursor.execute("SELECT current_balance FROM account_codes WHERE code = '1100'")
stored_balance = Decimal(str(cursor.fetchone()[0]))
print(f"Stored Balance:   Rs {stored_balance:,.2f}")
print(f"Difference:       Rs {abs(running - stored_balance):,.2f}")

# Now get all unpaid posted bills
print("\n" + "=" * 120)
print("ALL UNPAID POSTED BILLS")
print("=" * 120)

cursor.execute("""
    SELECT
        mb.bill_number,
        f.flat_number,
        mb.month,
        mb.year,
        mb.total_amount,
        mb.status
    FROM maintenance_bills mb
    JOIN flats f ON f.id = mb.flat_id
    WHERE mb.status = 'UNPAID' AND mb.is_posted = 1
    ORDER BY f.flat_number, mb.year, mb.month
""")
bills = cursor.fetchall()

print(f"\n{'Bill Number':<20} | {'Flat':<8} | {'Month/Year':<10} | {'Amount':>10} | Status")
print("-" * 80)

total_unpaid = Decimal(0)
for bill_num, flat_num, month, year, amount, status in bills:
    amount = Decimal(str(amount))
    total_unpaid += amount
    bill_num_str = bill_num or "NULL"
    print(f"{bill_num_str:<20} | {flat_num:<8} | {month}/{year:<8} | {amount:>10.2f} | {status}")

print("\n" + "=" * 120)
print(f"Total Unpaid Posted Bills: Rs {total_unpaid:,.2f}")
print(f"GL Balance:                Rs {running:,.2f}")
print(f"Discrepancy:               Rs {total_unpaid - running:,.2f}")

# Check if there are specific amounts that match
print("\n" + "=" * 120)
print("ANALYZING CREDITS (PAYMENTS) vs UNPAID BILLS")
print("=" * 120)

cursor.execute("""
    SELECT credit_amount, description
    FROM transactions
    WHERE account_code = '1100' AND credit_amount > 0
    ORDER BY date
""")
credits = cursor.fetchall()

print(f"\nCredits to Account 1100 (Payments received):")
for credit, desc in credits:
    credit = Decimal(str(credit))
    print(f"  Rs {credit:>10.2f} - {desc[:80]}")

# Check if any of these credits match unpaid bills
print(f"\nChecking if any UNPAID bills have matching payment amounts...")
for bill_num, flat_num, month, year, amount, status in bills:
    amount = Decimal(str(amount))
    for credit, desc in credits:
        credit_amt = Decimal(str(credit))
        if abs(amount - credit_amt) < Decimal('0.01'):
            print(f"  MATCH: {bill_num} (Rs {amount:,.2f}) <-> Credit Rs {credit_amt:,.2f}")
            print(f"         Bill: {flat_num} {month}/{year}")
            print(f"         Payment: {desc[:80]}")

conn.close()
