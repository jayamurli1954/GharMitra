# Double-Entry Accounting System - Fundamental Rules

This document outlines the fundamental rules of double-entry bookkeeping that are **MANDATORY** and **CANNOT BE IGNORED** in this system.

## Golden Rules

### Rule 1: General Ledger Debit MUST Equal Credit
**This is the FIRST GOLDEN RULE and cannot be violated.**

- The General Ledger is the source of all accounting data
- **Total Debit in General Ledger MUST equal Total Credit**
- If Debit ≠ Credit, the accounting system is broken
- This rule is enforced at transaction creation time:
  - Quick Entry: Validates that Debit = Credit before posting
  - Journal Voucher: Validates that Debit = Credit before posting

**Implementation:**
- All transactions are stored in the `Transaction` table
- Each transaction has `debit_amount` and `credit_amount` fields
- Quick Entry creates 2 transactions (expense/income account + cash/bank account)
- Journal Voucher creates multiple transactions (one per line)
- General Ledger sums all `debit_amount` and `credit_amount` from all transactions
- If totals don't match, it indicates a data integrity issue

### Rule 2: Trial Balance Must Use General Ledger Balances
**This is the SECOND GOLDEN RULE and cannot be violated.**

- Trial Balance must get net balance (debit or credit) **ONLY from General Ledger**
- Trial Balance cannot use any other source of data
- Trial Balance is a summary of General Ledger balances

**Implementation:**
- Trial Balance calculates balances from transactions (which form the General Ledger)
- For each account:
  - Start with opening balance
  - Add all transactions from Financial Year start to as_on_date
  - Calculate net balance (debit or credit)
  - Extract net balance for Trial Balance display

## Fundamental Rule: Double-Entry Principle

### All Journal Entries Must Have Minimum 2 Accounts
**This is the FUNDAMENTAL RULE and cannot be ignored.**

- Every journal entry must have **at least one debit and one credit**
- Debit total MUST equal Credit total
- Only then can the entry be posted

**Implementation:**

#### Quick Entry:
- Creates 2 transactions automatically:
  1. Expense/Income account (debit or credit)
  2. Cash/Bank account (opposite debit or credit)
- Validates: `debit_amount + second_debit_amount = credit_amount + second_credit_amount`
- If validation fails, transaction is rejected

#### Journal Voucher:
- User creates multiple lines (minimum 2)
- Each line must have either debit OR credit (not both, not neither)
- Validates:
  - At least 2 entries required
  - At least one debit entry
  - At least one credit entry
  - Total Debit = Total Credit
- If validation fails, journal entry is rejected

## Data Flow

```
Quick Entry / Journal Voucher
    ↓
Validation (Debit = Credit?)
    ↓ (if valid)
Transaction Table (stores all transactions)
    ↓
General Ledger (sums all transactions)
    ↓
Trial Balance (extracts net balances from General Ledger)
```

## Source of Truth

1. **Transaction Table**: Source of all accounting entries
   - Contains all transactions from Quick Entry and Journal Vouchers
   - Each transaction has debit_amount and credit_amount

2. **General Ledger**: Aggregation of all transactions
   - Sums all debit_amount and credit_amount
   - Must satisfy: Total Debit = Total Credit

3. **Trial Balance**: Summary of General Ledger
   - Extracts net balance (debit or credit) for each account
   - Must satisfy: Total Debit = Total Credit

## Validation Points

### At Transaction Creation:
- ✅ Quick Entry validates Debit = Credit before posting
- ✅ Journal Voucher validates Debit = Credit before posting
- ✅ Both validate minimum 2 accounts (one debit, one credit)

### At General Ledger Generation:
- ✅ Sums all transactions in the period
- ✅ Calculates Total Debit and Total Credit
- ✅ Logs error if Debit ≠ Credit (should never happen if validation works)

### At Trial Balance Generation:
- ✅ Uses General Ledger balances only
- ✅ Calculates net balance for each account
- ✅ Validates Total Debit = Total Credit

## Error Handling

If any of these rules are violated:
1. **Transaction Creation**: Transaction is rejected with error message
2. **General Ledger**: Error is logged (should never happen)
3. **Trial Balance**: Shows imbalance warning

## Files Implementing These Rules

- `backend/app/routes/transactions.py`: Quick Entry validation
- `backend/app/routes/journal.py`: Journal Voucher validation
- `backend/app/routes/reports.py`: General Ledger and Trial Balance generation
