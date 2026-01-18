
from sqlalchemy import case, literal_column
from sqlalchemy.sql import and_

# Test case syntax
try:
    c = case((literal_column('1') == 1, 10), else_=0)
    print("case((cond, val), else_=0) worked")
except Exception as e:
    print(f"case((cond, val), else_=0) failed: {e}")

try:
    c = case([(literal_column('1') == 1, 10)], else_=0)
    print("case([(cond, val)], else_=0) worked")
except Exception as e:
    print(f"case([(cond, val)], else_=0) failed: {e}")
