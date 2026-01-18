import sqlite3
from decimal import Decimal

# Connect to the database
conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

print("=" * 80)
print("ANALYZING BILL STATUS MISMATCHES")
print("=" * 80)

# Get total GL balance for Account 1100
cursor.execute("SELECT current_balance FROM account_codes WHERE code = '1100'")
gl_balance = Decimal(str(cursor.fetchone()[0]))
print(f"\n1. GL Account 1100 Balance: Rs {gl_balance:,.2f}")

# Get total unpaid posted bills
cursor.execute("""
    SELECT SUM(total_amount)
    FROM maintenance_bills
    WHERE status = 'UNPAID' AND is_posted = 1
""")
unpaid_total = Decimal(str(cursor.fetchone()[0] or 0))
print(f"2. Total Unpaid Posted Bills: Rs {unpaid_total:,.2f}")

difference = unpaid_total - gl_balance
print(f"3. Difference: Rs {difference:,.2f}")

print("\n" + "=" * 80)
print("DETAILED ANALYSIS: Finding Bills That Should Be PAID")
print("=" * 80)

# Get all credits to Account 1100 (payments reducing receivables)
cursor.execute("""
    SELECT
        t.document_number,
        t.transaction_date,
        t.amount,
        t.narration
    FROM transactions t
    WHERE t.account_code = '1100'
    AND t.transaction_type = 'CREDIT'
    ORDER BY t.transaction_date
""")
credits = cursor.fetchall()

print(f"\nFound {len(credits)} credit transactions to Account 1100:")
total_credits = Decimal('0')
for doc_num, date, amount, narration in credits:
    amount_dec = Decimal(str(amount))
    total_credits += amount_dec
    print(f"  {doc_num} | {date} | Rs {amount_dec:,.2f} | {narration}")

print(f"\nTotal Credits to Account 1100: Rs {total_credits:,.2f}")

# Get all debits to Account 1100 (bills increasing receivables)
cursor.execute("""
    SELECT
        t.document_number,
        t.transaction_date,
        t.amount,
        t.narration
    FROM transactions t
    WHERE t.account_code = '1100'
    AND t.transaction_type = 'DEBIT'
    AND t.is_posted = 1
    ORDER BY t.transaction_date
""")
debits = cursor.fetchall()

print(f"\nFound {len(debits)} posted debit transactions to Account 1100:")
total_debits = Decimal('0')
for doc_num, date, amount, narration in debits:
    amount_dec = Decimal(str(amount))
    total_debits += amount_dec

print(f"Total Posted Debits to Account 1100: Rs {total_debits:,.2f}")

calculated_balance = total_debits - total_credits
print(f"\nCalculated GL Balance (Debits - Credits): Rs {calculated_balance:,.2f}")
print(f"Actual GL Balance: Rs {gl_balance:,.2f}")
print(f"Difference: Rs {abs(calculated_balance - gl_balance):,.2f}")

print("\n" + "=" * 80)
print("CHECKING INDIVIDUAL FLAT BALANCES")
print("=" * 80)

# Get all flats and their unpaid bills vs GL entries
cursor.execute("""
    SELECT
        f.id,
        f.flat_number,
        u.full_name
    FROM flats f
    LEFT JOIN users u ON u.id = f.owner_id
    WHERE f.status = 'OCCUPIED'
    ORDER BY f.flat_number
""")
flats = cursor.fetchall()

total_mismatch = Decimal('0')
mismatches = []

for flat_id, flat_number, owner_name in flats:
    # Get unpaid posted bills for this flat
    cursor.execute("""
        SELECT SUM(total_amount)
        FROM maintenance_bills
        WHERE flat_id = ? AND status = 'UNPAID' AND is_posted = 1
    """, (flat_id,))
    unpaid_bills = Decimal(str(cursor.fetchone()[0] or 0))

    # Get debits to 1100 for this flat
    cursor.execute("""
        SELECT SUM(t.amount)
        FROM transactions t
        JOIN maintenance_bills mb ON t.document_number = mb.bill_number
        WHERE mb.flat_id = ?
        AND t.account_code = '1100'
        AND t.transaction_type = 'DEBIT'
        AND t.is_posted = 1
    """, (flat_id,))
    debits_result = cursor.fetchone()[0]
    flat_debits = Decimal(str(debits_result or 0))

    # Get credits to 1100 for this flat (through bill payments)
    cursor.execute("""
        SELECT SUM(p.amount)
        FROM payments p
        JOIN maintenance_bills mb ON p.bill_id = mb.id
        WHERE mb.flat_id = ?
    """, (flat_id,))
    credits_result = cursor.fetchone()[0]
    flat_credits = Decimal(str(credits_result or 0))

    # Expected balance from GL = debits - credits
    expected_from_gl = flat_debits - flat_credits

    if unpaid_bills != expected_from_gl and abs(unpaid_bills - expected_from_gl) > Decimal('0.01'):
        mismatch_amount = unpaid_bills - expected_from_gl
        total_mismatch += mismatch_amount
        mismatches.append({
            'flat_id': flat_id,
            'flat_number': flat_number,
            'owner': owner_name or 'N/A',
            'unpaid_bills': unpaid_bills,
            'expected': expected_from_gl,
            'mismatch': mismatch_amount
        })

if mismatches:
    print(f"\nFound {len(mismatches)} flats with mismatches:")
    for m in mismatches:
        print(f"\n  {m['flat_number']} ({m['owner']})")
        print(f"    Unpaid Bills: Rs {m['unpaid_bills']:,.2f}")
        print(f"    Expected from GL: Rs {m['expected']:,.2f}")
        print(f"    Mismatch: Rs {m['mismatch']:,.2f}")

        # Show the bills for this flat
        cursor.execute("""
            SELECT bill_number, month, year, total_amount, status, is_posted
            FROM maintenance_bills
            WHERE flat_id = ?
            ORDER BY year DESC, month DESC
        """, (m['flat_id'],))
        bills = cursor.fetchall()
        print(f"    Bills:")
        for bill_num, month, year, amount, status, posted in bills:
            posted_str = "POSTED" if posted else "NOT POSTED"
            print(f"      {bill_num} | {month}/{year} | Rs {amount:,.2f} | {status} | {posted_str}")
else:
    print("\nNo flat-level mismatches found.")

print(f"\nTotal mismatch across all flats: Rs {total_mismatch:,.2f}")

# Check if there are any PAID bills that were actually posted to GL
print("\n" + "=" * 80)
print("CHECKING PAID BILLS")
print("=" * 80)

cursor.execute("""
    SELECT
        mb.bill_number,
        f.flat_number,
        mb.month,
        mb.year,
        mb.total_amount,
        mb.status,
        mb.is_posted,
        mb.paid_date
    FROM maintenance_bills mb
    JOIN flats f ON f.id = mb.flat_id
    WHERE mb.status = 'PAID' AND mb.is_posted = 1
    ORDER BY mb.year DESC, mb.month DESC
""")
paid_bills = cursor.fetchall()

print(f"\nFound {len(paid_bills)} PAID and POSTED bills:")
total_paid_posted = Decimal('0')
for bill_num, flat_num, month, year, amount, status, posted, paid_date in paid_bills:
    amount_dec = Decimal(str(amount))
    total_paid_posted += amount_dec
    print(f"  {bill_num} | {flat_num} | {month}/{year} | Rs {amount_dec:,.2f} | Paid: {paid_date}")

print(f"\nTotal amount of PAID posted bills: Rs {total_paid_posted:,.2f}")

conn.close()

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"GL Account 1100 Balance: Rs {gl_balance:,.2f}")
print(f"Unpaid Posted Bills Total: Rs {unpaid_total:,.2f}")
print(f"Discrepancy: Rs {difference:,.2f}")
print(f"\nThis discrepancy suggests bills marked UNPAID that should be PAID.")
print("=" * 80)
