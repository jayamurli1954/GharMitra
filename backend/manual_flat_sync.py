"""
Manual Flat Sync Script
This script will sync flats based on the current blocks_config in society_settings
"""
import sqlite3
import json
from datetime import datetime
import sys

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Connect to database
db_path = "gharmitra.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("MANUAL FLAT SYNC DIAGNOSTIC")
print("=" * 80)

# 1. Check current blocks_config
print("\n1. Checking current blocks_config...")
cursor.execute("SELECT blocks_config FROM society_settings WHERE society_id = 1")
result = cursor.fetchone()
if result and result[0]:
    blocks_config = json.loads(result[0])
    print(f"   blocks_config: {blocks_config}")
else:
    print("   No blocks_config found!")
    blocks_config = []

# 2. Calculate expected flats
print("\n2. Calculating expected flats based on blocks_config...")
expected_flat_numbers = set()

for block in blocks_config:
    block_name = block.get('name')
    floors = int(block.get('floors', 0))
    flats_per_floor = int(block.get('flatsPerFloor', 0))

    print(f"   Block {block_name}: {floors} floors × {flats_per_floor} flats/floor")

    if not block_name or floors <= 0 or flats_per_floor <= 0:
        continue

    for floor in range(1, floors + 1):
        for flat_seq in range(1, flats_per_floor + 1):
            flat_num_local = (floor * 100) + flat_seq
            full_flat_number = f"{block_name}-{flat_num_local}"
            expected_flat_numbers.add(full_flat_number)

print(f"   Expected total: {len(expected_flat_numbers)} flats")
if expected_flat_numbers:
    sorted_expected = sorted(list(expected_flat_numbers))
    print(f"   Sample: {sorted_expected[:5]} ... {sorted_expected[-5:]}")

# 3. Check existing flats
print("\n3. Checking existing flats in database...")
cursor.execute("SELECT id, flat_number FROM flats WHERE society_id = 1 ORDER BY flat_number")
existing_flats = cursor.fetchall()
existing_flat_numbers = {flat[1] for flat in existing_flats}

print(f"   Existing total: {len(existing_flats)} flats")
if existing_flat_numbers:
    sorted_existing = sorted(list(existing_flat_numbers))
    print(f"   Sample: {sorted_existing[:5]} ... {sorted_existing[-5:]}")

# 4. Calculate flats to delete
print("\n4. Calculating flats to delete...")
flats_to_delete = [(flat_id, flat_number) for flat_id, flat_number in existing_flats
                   if flat_number not in expected_flat_numbers]

print(f"   Flats to delete: {len(flats_to_delete)}")
if flats_to_delete:
    print(f"   List: {[f[1] for f in flats_to_delete]}")

# 5. Check if flats have members
if flats_to_delete:
    print("\n5. Checking if flats to delete have active members...")
    flat_ids_to_delete = [f[0] for f in flats_to_delete]
    placeholders = ','.join('?' * len(flat_ids_to_delete))
    cursor.execute(
        f"SELECT COUNT(*) FROM members WHERE flat_id IN ({placeholders}) AND status = 'active'",
        flat_ids_to_delete
    )
    active_members_count = cursor.fetchone()[0]
    print(f"   Active members in flats to delete: {active_members_count}")

    if active_members_count > 0:
        print("   ⚠️ CANNOT DELETE: Flats have active members!")
    else:
        print("   ✓ Safe to delete: No active members")

# 6. Calculate deletion percentage
print("\n6. Safety check - deletion percentage...")
if existing_flats:
    deletion_percentage = (len(flats_to_delete) / len(existing_flats) * 100)
    print(f"   Deletion percentage: {deletion_percentage:.1f}%")

    if deletion_percentage > 50 and len(existing_flats) > 10:
        print(f"   ⚠️ SAFETY CHECK FAILED: Attempting to delete {len(flats_to_delete)} flats ({deletion_percentage:.1f}% of total)")
        print("   This exceeds the 50% safety threshold!")
    else:
        print("   ✓ Safety check passed")

# 7. Offer to perform deletion
print("\n7. Action required...")
if not flats_to_delete:
    print("   ✓ No action needed - flats already match configuration")
elif active_members_count > 0:
    print("   ✗ Cannot delete flats - they have active members")
    print("   Action: Remove members first, then retry")
elif deletion_percentage > 50 and len(existing_flats) > 10:
    print(f"   ✗ Cannot delete - exceeds 50% safety threshold")
    print("   Action: This script can override the safety check if needed")
    print("\n   Do you want to DELETE these flats? (yes/no): ", end="")
    response = input().strip().lower()

    if response == 'yes':
        print("\n   Deleting flats...")
        for flat_id, flat_number in flats_to_delete:
            cursor.execute("DELETE FROM flats WHERE id = ?", (flat_id,))
            print(f"   ✓ Deleted {flat_number}")

        conn.commit()
        print(f"\n   ✓ Successfully deleted {len(flats_to_delete)} flats")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM flats WHERE society_id = 1")
        remaining = cursor.fetchone()[0]
        print(f"   Remaining flats: {remaining}")
    else:
        print("   Deletion cancelled")
else:
    print(f"   Ready to delete {len(flats_to_delete)} flats")
    print("\n   Do you want to DELETE these flats? (yes/no): ", end="")
    response = input().strip().lower()

    if response == 'yes':
        print("\n   Deleting flats...")
        for flat_id, flat_number in flats_to_delete:
            cursor.execute("DELETE FROM flats WHERE id = ?", (flat_id,))
            print(f"   ✓ Deleted {flat_number}")

        conn.commit()
        print(f"\n   ✓ Successfully deleted {len(flats_to_delete)} flats")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM flats WHERE society_id = 1")
        remaining = cursor.fetchone()[0]
        print(f"   Remaining flats: {remaining}")
    else:
        print("   Deletion cancelled")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

conn.close()
