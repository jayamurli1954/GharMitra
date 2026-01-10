# Voucher Numbering System Changes

## Summary

Simplified voucher numbering system to use sequential numbers instead of date-based numbering:
- **Quick Entry**: QV-0001, QV-0002, QV-0003, etc.
- **Journal Voucher**: JV-0001, JV-0002, JV-0003, etc.
- **Receipt Voucher**: RV-0001, RV-0002, RV-0003, etc. (for maintenance bill payments)

## Changes Made

### 1. Document Numbering Utility (`backend/app/utils/document_numbering.py`)

**New Functions:**
- `generate_quick_entry_voucher_number()`: Generates QV-0001, QV-0002, etc. (sequential)
- `generate_journal_voucher_number()`: Generates JV-0001, JV-0002, etc. (sequential)
- `generate_receipt_voucher_number()`: Generates RV-0001, RV-0002, etc. (sequential)

**Updated Legacy Functions:**
- `generate_transaction_document_number()`: Now calls `generate_quick_entry_voucher_number()` (backward compatible)
- `generate_journal_entry_number()`: Now calls `generate_journal_voucher_number()` (backward compatible)

### 2. Payment Receipt Numbering (`backend/app/routes/payments.py`)

**Updated:**
- `generate_receipt_number()`: Now uses `generate_receipt_voucher_number()` to generate RV-0001 format
- Changed from financial year-based format (RCT/2024-25/001) to simple sequential format (RV-0001)

### 3. Transaction Routes (`backend/app/routes/transactions.py`)

**Automatic:**
- Quick Entry transactions automatically use QV-0001 format via `generate_transaction_document_number()`

### 4. Journal Entry Routes (`backend/app/routes/journal.py`)

**Automatic:**
- Journal Voucher entries automatically use JV-0001 format via `generate_journal_entry_number()`

## Numbering Logic

All voucher numbers are:
- **Sequential**: Increment from 0001, 0002, 0003, etc.
- **Society-specific**: Each society has its own sequence
- **Persistent**: Numbers continue across all time (not reset daily/monthly)
- **Format**: `{PREFIX}-{NUMBER}` where NUMBER is 4 digits with leading zeros

## Examples

### Quick Entry
- First transaction: QV-0001
- Second transaction: QV-0002
- Third transaction: QV-0003

### Journal Voucher
- First voucher: JV-0001
- Second voucher: JV-0002
- Third voucher: JV-0003

### Receipt Voucher
- First payment: RV-0001
- Second payment: RV-0002
- Third payment: RV-0003

## Migration Notes

- Existing transactions with old numbering (TXN-YYYYMMDD-001, JE-YYYYMMDD-001) will remain unchanged
- New transactions will use the new sequential numbering
- Receipt numbers will change from RCT/2024-25/001 format to RV-0001 format

## Testing Checklist

- [ ] Create Quick Entry transaction → Verify QV-0001 format
- [ ] Create Journal Voucher → Verify JV-0001 format
- [ ] Record maintenance payment → Verify RV-0001 format
- [ ] Verify sequential numbering (QV-0002, QV-0003, etc.)
- [ ] Verify society-specific numbering (different societies have separate sequences)
- [ ] Check existing transactions still display correctly
