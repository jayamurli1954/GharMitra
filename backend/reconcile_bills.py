import sqlite3
from decimal import Decimal

# Connect to the database
conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

print("=" * 80)
print("RECONCILING MAINTENANCE BILLS WITH GL ACCOUNT 1100")
print("=" * 80)

# Step 1: Get GL balance
cursor.execute("SELECT current_balance FROM account_codes WHERE code = '1100'")
gl_balance = Decimal(str(cursor.fetchone()[0]))
print(f"\nGL Account 1100 Balance: Rs {gl_balance:,.2f}")

# Step 2: Calculate from transactions table
cursor.execute("""
    SELECT SUM(debit_amount - credit_amount)
    FROM transactions
    WHERE account_code = '1100'
""")
calculated_balance = Decimal(str(cursor.fetchone()[0] or 0))
print(f"Calculated from Transactions (Debits - Credits): Rs {calculated_balance:,.2f}")

# Step 3: Get unpaid posted bills total
cursor.execute("""
    SELECT SUM(total_amount)
    FROM maintenance_bills
    WHERE status = 'UNPAID' AND is_posted = 1
""")
unpaid_posted_total = Decimal(str(cursor.fetchone()[0] or 0))
print(f"Total Unpaid Posted Bills: Rs {unpaid_posted_total:,.2f}")

difference = unpaid_posted_total - gl_balance
print(f"\nDiscrepancy: Rs {difference:,.2f}")

print("\n" + "=" * 80)
print("ANALYZING EACH FLAT'S BILLS AND GL TRANSACTIONS")
print("=" * 80)

# Get all flats
cursor.execute("""
    SELECT id, flat_number, owner_name
    FROM flats
    WHERE occupancy_status = 'OCCUPIED'
    ORDER BY flat_number
""")
flats = cursor.fetchall()

bills_to_fix = []

for flat_id, flat_number, owner_name in flats:
    # Get all posted bills for this flat
    cursor.execute("""
        SELECT
            id,
            bill_number,
            month,
            year,
            total_amount,
            status,
            is_posted
        FROM maintenance_bills
        WHERE flat_id = ?
        AND is_posted = 1
        ORDER BY year DESC, month DESC
    """, (flat_id,))
    bills = cursor.fetchall()

    if not bills:
        continue

    # Get total debits to 1100 for this flat (bills raised)
    cursor.execute("""
        SELECT SUM(debit_amount)
        FROM transactions
        WHERE account_code = '1100'
        AND description LIKE ?
    """, (f'%Flat: {flat_number}%',))
    total_debits = Decimal(str(cursor.fetchone()[0] or 0))

    # Get total credits to 1100 for this flat (payments received)
    cursor.execute("""
        SELECT SUM(credit_amount)
        FROM transactions
        WHERE account_code = '1100'
        AND description LIKE ?
    """, (f'%from {flat_number}%',))
    total_credits = Decimal(str(cursor.fetchone()[0] or 0))

    # Expected unpaid = debits - credits
    expected_unpaid = total_debits - total_credits

    # Actual unpaid from bills table
    actual_unpaid = sum(Decimal(str(bill[4])) for bill in bills if bill[5] == 'UNPAID')

    if abs(expected_unpaid - actual_unpaid) > Decimal('0.01'):
        print(f"\n{flat_number} ({owner_name or 'N/A'})")
        print(f"  GL: Debits Rs {total_debits:,.2f} - Credits Rs {total_credits:,.2f} = Rs {expected_unpaid:,.2f}")
        print(f"  Bills: Rs {actual_unpaid:,.2f} unpaid")
        print(f"  Difference: Rs {actual_unpaid - expected_unpaid:,.2f}")
        print(f"  Bills:")

        # Show all bills for this flat
        for bill_id, bill_num, month, year, amount, status, posted in bills:
            amount_dec = Decimal(str(amount))
            print(f"    {bill_num} | {month}/{year} | Rs {amount_dec:,.2f} | {status}")

            # Check if there's a payment for this bill
            cursor.execute("""
                SELECT SUM(credit_amount)
                FROM transactions
                WHERE account_code = '1100'
                AND description LIKE ?
                AND credit_amount = ?
            """, (f'%{flat_number}%', float(amount_dec)))
            payment = cursor.fetchone()[0]

            if payment and status == 'UNPAID':
                print(f"      -> ISSUE: Bill is UNPAID but has payment of Rs {payment:,.2f}")
                bills_to_fix.append({
                    'bill_id': bill_id,
                    'bill_number': bill_num,
                    'flat_number': flat_number,
                    'amount': amount_dec,
                    'month': month,
                    'year': year
                })

print("\n" + "=" * 80)
print("BILLS THAT NEED STATUS UPDATE")
print("=" * 80)

if bills_to_fix:
    print(f"\nFound {len(bills_to_fix)} bills that should be marked as PAID:")
    for bill in bills_to_fix:
        print(f"  {bill['bill_number']} | {bill['flat_number']} | {bill['month']}/{bill['year']} | Rs {bill['amount']:,.2f}")

    print("\n" + "=" * 80)
    print("FIXING BILL STATUSES")
    print("=" * 80)

    for bill in bills_to_fix:
        cursor.execute("""
            UPDATE maintenance_bills
            SET status = 'PAID', paid_date = '2026-01-10'
            WHERE id = ?
        """, (bill['bill_id'],))
        print(f"  Updated {bill['bill_number']} to PAID")

    conn.commit()
    print(f"\nSuccessfully updated {len(bills_to_fix)} bills to PAID status")

    # Verify the fix
    cursor.execute("""
        SELECT SUM(total_amount)
        FROM maintenance_bills
        WHERE status = 'UNPAID' AND is_posted = 1
    """)
    new_unpaid_total = Decimal(str(cursor.fetchone()[0] or 0))
    print(f"\nAfter fix:")
    print(f"  GL Balance: Rs {gl_balance:,.2f}")
    print(f"  Unpaid Posted Bills: Rs {new_unpaid_total:,.2f}")
    print(f"  Difference: Rs {abs(new_unpaid_total - gl_balance):,.2f}")
else:
    print("\nNo bills found that need status updates based on payment matching.")
    print("The discrepancy may be due to:")
    print("  1. Partial payments")
    print("  2. Bills with different amounts than payments")
    print("  3. Credits/reversals that affected the GL but not bill status")

conn.close()
print("\n" + "=" * 80)
