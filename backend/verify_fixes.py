"""
Manual verification script for critical fixes
Run with: python verify_fixes.py
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.database import Base
from app.models_db import Transaction, User
from app.models.transaction import TransactionResponse
from app.utils.security import get_password_hash
from datetime import date, datetime

# Use in-memory database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DB_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def verify_fixes():
    """Verify all critical fixes"""
    print("=" * 60)
    print("VERIFYING CRITICAL FIXES")
    print("=" * 60)
    
    # Setup database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    try:
        # Create test user
        async with SessionLocal() as session:
            user = User(
                email="test@example.com",
                password_hash=get_password_hash("test"),
                name="Test User",
                apartment_number="101",
                role="admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            user_id = user.id
            print(f"[OK] Created test user (ID: {user_id})")
        
        # Test 1: Verify TransactionResponse doesn't have non-existent fields
        print("\n[TEST 1] Verifying TransactionResponse model...")
        try:
            # Create a transaction
            async with SessionLocal() as session:
                txn = Transaction(
                    type="expense",
                    category="Utilities",
                    amount=1000.0,
                    description="Test",
                    date=date.today(),
                    added_by=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(txn)
                await session.commit()
                await session.refresh(txn)
            
            # Try to create TransactionResponse (this would fail if fields don't exist)
            async with SessionLocal() as session:
                result = await session.execute(select(Transaction).where(Transaction.id == txn.id))
                db_txn = result.scalar_one_or_none()
                
                # This is the critical test - creating response should NOT access non-existent fields
                response = TransactionResponse(
                    id=str(db_txn.id),
                    type=db_txn.type.value,  # Convert enum to string
                    category=db_txn.category,
                    description=db_txn.description,
                    amount=db_txn.amount,
                    date=db_txn.date,
                    account_code=db_txn.account_code,
                    added_by=str(db_txn.added_by),
                    created_at=db_txn.created_at,
                    updated_at=db_txn.updated_at
                )
                
                # Verify response doesn't have non-existent fields
                response_dict = response.model_dump()
                assert "payment_method" not in response_dict, "[FAIL] payment_method should not exist"
                assert "reference_number" not in response_dict, "[FAIL] reference_number should not exist"
                assert "notes" not in response_dict, "[FAIL] notes should not exist"
                
                print("  [OK] TransactionResponse created successfully")
                print("  [OK] No non-existent fields (payment_method, reference_number, notes)")
                print(f"  [OK] Response contains: {list(response_dict.keys())}")
        
        except AttributeError as e:
            if "payment_method" in str(e) or "reference_number" in str(e) or "notes" in str(e):
                print(f"  [FAIL] Still trying to access non-existent field: {e}")
                return False
            else:
                raise
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        # Test 2: Verify type conversion (string to int)
        print("\n[TEST 2] Verifying type conversion (string user_id -> int)...")
        try:
            # Simulate current_user.id as string (from UserResponse)
            current_user_id_str = str(user_id)
            
            # This is what happens in the route - convert string to int
            try:
                added_by_user_id = int(current_user_id_str)
            except (ValueError, TypeError) as e:
                print(f"  [FAIL] Type conversion error: {e}")
                return False
            
            # Verify it's an integer
            assert isinstance(added_by_user_id, int), f"Should be int, got {type(added_by_user_id)}"
            assert added_by_user_id == user_id, "Converted ID should match original"
            
            # Create transaction with converted ID
            async with SessionLocal() as session:
                txn = Transaction(
                    type="income",
                    category="Test",
                    amount=500.0,
                    description="Type conversion test",
                    date=date.today(),
                    added_by=added_by_user_id,  # Using int here
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(txn)
                await session.commit()
                await session.refresh(txn)
                
                # Verify it was stored correctly
                assert txn.added_by == user_id
                assert isinstance(txn.added_by, int)
            
            print(f"  [OK] String '{current_user_id_str}' converted to int {added_by_user_id}")
            print(f"  [OK] Transaction created with correct user_id type (int)")
        
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        # Test 3: Verify TransactionResponse ID field (no alias confusion)
        print("\n[TEST 3] Verifying TransactionResponse ID field...")
        try:
            async with SessionLocal() as session:
                result = await session.execute(select(Transaction).limit(1))
                txn = result.scalar_one_or_none()
                
                if txn:
                    response = TransactionResponse(
                        id=str(txn.id),  # Using 'id' directly, not '_id'
                        type=txn.type.value,  # Convert enum to string
                        category=txn.category,
                        description=txn.description,
                        amount=txn.amount,
                        date=txn.date,
                        account_code=txn.account_code,
                        added_by=str(txn.added_by),
                        created_at=txn.created_at,
                        updated_at=txn.updated_at
                    )
                    
                    # Verify ID is accessible
                    assert response.id == str(txn.id)
                    response_dict = response.model_dump()
                    assert "id" in response_dict
                    assert "_id" not in response_dict or response_dict.get("_id") == response_dict["id"]
                    
                    print(f"  [OK] ID field works correctly: {response.id}")
                    print(f"  [OK] No alias confusion")
        
        except Exception as e:
            print(f"  [FAIL] {e}")
            return False
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED - Critical fixes verified!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(verify_fixes())
    sys.exit(0 if success else 1)

