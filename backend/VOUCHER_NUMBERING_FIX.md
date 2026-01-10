# Voucher Numbering Fix - Single Voucher Number per Entry

## Summary

Fixed voucher numbering to ensure:
1. **Maintenance Bill Posting**: All bills posted as ONE Journal Voucher (JV) with one JV number
2. **Quick Entry**: One voucher number (QV) for the entire entry (both debit and credit transactions)
3. **No Sub-numbers**: Transactions no longer have individual document numbers - they all reference the same voucher number

## Changes Made

### 1. Maintenance Bill Posting (`backend/app/routes/maintenance.py`)

**Before:**
- Each transaction had its own document number (TXN-YYYYMMDD-AR, TXN-YYYYMMDD-MNT, etc.)
- Multiple transactions with different document numbers

**After:**
- All transactions reference the same JV number (from JournalEntry.entry_number)
- Transactions have `document_number=None` (no individual numbers)
- One JV number for all debit and credit entries in the bill posting

**Key Changes:**
- Removed `document_number` parameter from `create_txn()` function
- Set `document_number=None` for all transactions
- All transactions linked to the same `journal_entry_id` (which has the JV number)

### 2. Quick Entry (`backend/app/routes/transactions.py`)

**Before:**
- Two transactions with different QV numbers (QV-0001, QV-0002 using offset)
- Each transaction had its own document number

**After:**
- Both transactions reference the same QV number
- QV number is used as the Journal Entry number
- Transactions have `document_number=None` (no individual numbers)

**Key Changes:**
- Removed offset parameter usage
- Use single QV number for both transactions
- Set `document_number=None` for both transactions
- Both transactions linked to the same `journal_entry_id` (which has the QV number)

### 3. Regenerate Bill (`backend/app/routes/maintenance.py`)

**Updated:**
- Transactions now have `document_number=None`
- Both transactions reference the same JV number

### 4. Reverse Bill (`backend/app/routes/maintenance.py`)

**Updated:**
- Reversal transactions now have `document_number=None`
- Both reversal transactions reference the same JV number

## Voucher Number Format

- **Quick Entry**: QV-0001, QV-0002, etc. (used as Journal Entry number)
- **Journal Voucher**: JV-0001, JV-0002, etc. (Journal Entry number)
- **Receipt Voucher**: RV-0001, RV-0002, etc. (Payment receipt number)

## Transaction Structure

All transactions now:
- Have `document_number=None` (no individual document numbers)
- Reference the voucher number via `journal_entry_id` → `JournalEntry.entry_number`
- Are grouped under one voucher number for the entire entry

## Example

### Maintenance Bill Posting
- **Journal Entry**: JV-0001
- **Transactions**:
  - Debit 1100 (Flat A-101): References JV-0001
  - Debit 1100 (Flat A-102): References JV-0001
  - Credit 4000: References JV-0001
- **Result**: One JV number (JV-0001) for all transactions

### Quick Entry
- **Journal Entry**: QV-0001
- **Transactions**:
  - Debit Expense Account: References QV-0001
  - Credit Cash/Bank: References QV-0001
- **Result**: One QV number (QV-0001) for both transactions

## Benefits

1. **Simplified Tracking**: One voucher number per entry, easy to reference
2. **No Sub-numbers**: All transactions in an entry share the same voucher number
3. **Clear Grouping**: All transactions clearly grouped under one voucher
4. **Consistent Format**: QV for Quick Entry, JV for Journal Voucher, RV for Receipt Voucher

## Testing Checklist

- [ ] Post maintenance bills → Verify one JV number for all transactions
- [ ] Create Quick Entry → Verify one QV number for both transactions
- [ ] Create Journal Voucher → Verify one JV number for all entries
- [ ] Regenerate bill → Verify one JV number for both transactions
- [ ] Reverse bill → Verify one JV number for both reversal transactions
- [ ] Verify transactions show voucher number (not individual document numbers)
- [ ] Verify no sub-numbers (1, 2, 3) appear in transaction lists
