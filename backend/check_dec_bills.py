import sqlite3
from decimal import Decimal

conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

print("=" * 80)
print("ALL DECEMBER 2025 POSTED BILLS")
print("=" * 80)

cursor.execute("""
    SELECT f.flat_number, mb.bill_number, mb.total_amount, mb.status
    FROM maintenance_bills mb
    JOIN flats f ON f.id = mb.flat_id
    WHERE mb.month = 12 AND mb.year = 2025 AND mb.is_posted = 1
    ORDER BY f.flat_number
""")
bills = cursor.fetchall()

total_all = Decimal(0)
total_unpaid = Decimal(0)

print(f"\n{'Flat':<8} | {'Bill Number':<20} | {'Amount':>10} | Status")
print("-" * 60)

for flat, bill_num, amt, status in bills:
    amt = Decimal(str(amt))
    total_all += amt
    if status == 'UNPAID':
        total_unpaid += amt
    bill_num_str = bill_num or "NULL"
    print(f"{flat:<8} | {bill_num_str:<20} | {amt:>10.2f} | {status}")

print("\n" + "=" * 80)
print(f"Total ALL Posted Bills: Rs {total_all:,.2f}")
print(f"Total UNPAID Bills: Rs {total_unpaid:,.2f}")

# Check GL debits for December 2025
cursor.execute("""
    SELECT SUM(debit_amount)
    FROM transactions
    WHERE account_code = '1100'
    AND date >= '2026-01-01'
    AND date < '2026-01-10'
    AND debit_amount > 0
""")
gl_debits = Decimal(str(cursor.fetchone()[0] or 0))

print(f"\nGL Debits (posted bills) for Dec 2025: Rs {gl_debits:,.2f}")
print(f"Difference (GL Debits - Total Bills): Rs {gl_debits - total_all:,.2f}")

# Show the detailed GL transactions
print("\n" + "=" * 80)
print("DETAILED GL DEBITS FOR DECEMBER 2025")
print("=" * 80)

cursor.execute("""
    SELECT date, debit_amount, description
    FROM transactions
    WHERE account_code = '1100'
    AND date >= '2026-01-01'
    AND date < '2026-01-10'
    AND debit_amount > 0
    ORDER BY date, description
""")
txns = cursor.fetchall()

total_debits = Decimal(0)
for date, debit, desc in txns:
    debit = Decimal(str(debit))
    total_debits += debit
    print(f"{date} | {debit:>10.2f} | {desc[:60]}")

print(f"\nTotal GL Debits: Rs {total_debits:,.2f}")

# Find the duplicate
print("\n" + "=" * 80)
print("LOOKING FOR A-101 DUPLICATES")
print("=" * 80)

cursor.execute("""
    SELECT date, debit_amount, credit_amount, description
    FROM transactions
    WHERE account_code = '1100'
    AND (description LIKE '%A-101%' OR description LIKE '%Flat A-101%')
    ORDER BY date
""")
a101_txns = cursor.fetchall()

print(f"\n{'Date':<12} | {'Debit':>10} | {'Credit':>10} | Description")
print("-" * 100)
total_a101_debit = Decimal(0)
total_a101_credit = Decimal(0)
for date, debit, credit, desc in a101_txns:
    debit = Decimal(str(debit))
    credit = Decimal(str(credit))
    total_a101_debit += debit
    total_a101_credit += credit
    print(f"{date:<12} | {debit:>10.2f} | {credit:>10.2f} | {desc}")

print("\n" + "=" * 80)
print(f"A-101 Total Debits: Rs {total_a101_debit:,.2f}")
print(f"A-101 Total Credits: Rs {total_a101_credit:,.2f}")
print(f"A-101 Net Balance: Rs {total_a101_debit - total_a101_credit:,.2f}")

print("\nA-101 should only have ONE debit of Rs 3,135 for December 2025")
print(f"But GL shows total debits of Rs {total_a101_debit:,.2f}")
print(f"Extra debits: Rs {total_a101_debit - Decimal('3135'):,.2f}")

conn.close()
