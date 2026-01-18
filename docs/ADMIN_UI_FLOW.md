## ADMIN UI FLOW ##

## (A) Tenant Move-In ##

Owner → Add Tenant Request
        |
Admin → Verify Rent Agreement (physical)
Admin → Verify Police Form (physical)
        |
[✔ Documents Verified]
        |
Tenant Status → ACTIVE

## (B) Tenant Move-Out ##

Tenant → Request Vacate
        |
System → Generate Final Bill
        |
Payment Received?
        |
NO → Block Vacate
YES → Tenant Status → INACTIVE


## (C) Owner Transfer (Sale) ##

Owner → Request Transfer
        |
System → Check Flat Balance
        |
If Balance ≠ 0 → BLOCK
If Balance = 0 → Generate NDC
        |
Admin → Approve Transfer
        |
New Owner Activated


## (D) Admin Dashboard View  ##

Flat A-203
Owner: Ramesh Kumar
Tenant: Suresh (Active)
Outstanding: ₹ 0 ✔
Documents: Verified ✔
[ Issue NDC ]
[ Transfer Ownership ]


