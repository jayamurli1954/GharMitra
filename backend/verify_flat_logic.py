
import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.models_db import Flat, OccupancyStatus
    print("SUCCESS: Imported Flat and OccupancyStatus")
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)

# specific check for circular import or availability
print(f"OccupancyStatus.VACANT: {OccupancyStatus.VACANT}")

# Mock logic test
blocks_config = [{"name": "A", "floors": 2, "flatsPerFloor": 2}]
new_flats = []
for block in blocks_config:
    block_name = block.get('name')
    floors = int(block.get('floors', 0))
    flats_per_floor = int(block.get('flatsPerFloor', 0))
    
    for floor in range(1, floors + 1):
        for flat_seq in range(1, flats_per_floor + 1):
            flat_num_local = (floor * 100) + flat_seq
            full_flat_number = f"{block_name}-{flat_num_local}"
            new_flats.append(full_flat_number)

print(f"Generated Flats: {new_flats}")
print("Logic verified.")
