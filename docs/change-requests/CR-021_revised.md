CHANGE REQUEST (CR)



CR ID: CR-2026-01-07-021_revised

Project: GharMitra – Housing Society ERP

Submitted By: Product Owner (SanMitra Tech Solutions)

Date Submitted: 2026-01-09

Priority: Critical

Type: Compliance / Data Integrity

Status: Submitted



#### 1\. CHANGE SUMMARY

Current Situation



GharMitra currently does not have a legally compliant and standardized monthly maintenance billing engine. Billing is not yet based on square-foot area, number of residents, or Indian society accounting norms.



#### Requested Change :



Implement a Monthly Maintenance Billing Engine that:  

Monthly maintenance Billing has different types each society has its way of calculating the maintenance billing so the maintenance Bling Engine has to be flexible and should have all the option so that committee will opt for the best suited option for them 



1. Calculates maintenance based on sq.ft × rate -> Admin input required.if not calculated based on area the rate should be '0'
   
**2.** Calculates on Per Person water charges + Calculates total Expenses for the Bill period (here admin input required as to which expenses to be included and which should excluded. Calculates water charges per resident -> Add Total water charges for the month of bill period that is total of  **5110 Water Charges - Tanker + 5120  Water Charges - Government  ÷ total inmates × per flat inmates for example total water charges = 30000  total inmates 60 then per person water charges = 30000 ÷ 60 =500 this is per person water charges. If Flat A-101 has 4 inmates/member then Flat A-101 water charges = 500 × 4 = 2000. Before arriving total inmates any addition or deduction of inmates /members  due to additional guest or inmates going on long vacation  for more than 7 days to be adjusted. hence Admin input is required arriving total inmates.** 

**2(a).** Fixed expenses may be applied equal per-flat charges or  based on area - If equal total expenses **÷ total no of flats  or if by area total expenses ÷ total area x flat area say if it is equal per flat. 25000 ÷ 20 = 1250 if by area 25000 ÷ 25000 = 1 x 1250 (area A-101) = 1250** the system should look out for in the Journal Vocher or Quick entry voucher place holder mentioning Expense for the month. If I have selected month as December and Year as 2025 for bill generation,  system should check in the place holder whether it has mentioned December, 2025  if it is there then that expense account (leaving out 5110 and 5120) should be displayed and admin will check the box to include it  for calculation. it can be equal or sq.ft. If equal total fixed   expenses ÷  total number of flat  for example   40000 ÷ 20 = 2000 if selected sq ft then  40000 ÷  25000  = 1.6 x 1260 (flat A-101) = 2016 (this amount varies as per sq, ft area and total all the flat added up should match or equal to 40000)


**3.** Calculates sinking fund per sq.ft or per flat as per Input
In bill generating page if this place holder is left blank and check the amount mentioned in setting page billing rules


**4.** Calculates repair fund per flat or per sq. ft. as per Input
In bill generating page if this place holder is left blank and check the amount mentioned in setting page billing rules



**5.** Calculates Corpus fund per flat or per sq. ft. as per Input
In bill generating page if this place holder is left blank and check the amount mentioned in setting page billing rules



#### Accounting Rule :



After the bill is generated    4000  Maintenance Charges  to be credited  and   1100	Maintenance Dues Receivable to be debited  System has to check credit = debit no difference

system also has to post this bill amount to individual member against their Flat ID. This posting is required for knowing  and tracking individual flat ID dues and follow up for collection .

when payment made by the member,  1100	 Maintenance Dues Receivable to be credited  and  1001 HDFC Bank - Main Account or  1010  Cash in Hand as the case may be to be debited   there should also an entry in the Members Due register so this will reduce their balance.

Its a double entry accounting system debit = credit  if it is do not match no account posting should not carried out and a appropriate warning message to be displayed.

System should  ensure that  1100	 Maintenance Dues Receivable  is always matches members due register (Please note Members register is not part of Trial Balance or General ledger.)

validation : Once a bill is geneated for a particualar month say December, 2025 then again it cannot gnerated there should be a message Bill for the month of December, 2025 is generated Only January 2026 bill can be generated. Without generating bill for January 2026 February 2026 bill cannot be generated only after generating January 2026 February 2026 can be generated.

**Important Note** Dispute Redressal
if there is a dispute by a particular Flat  against a water charges or any other calculation there should be an option to revise the bill for that particcualr Flat.  For that, bill of that particualr flat only can be reversed and regenerated by manual input and then can be posted again with  a proper  explanation to be written in the note  for Audit compliance for reason of reversal and re generation

proper reversal Journal voucher has to be posted By debiting 4000  Maintenance Charges  and crediting   1100	Maintenance Dues Receivable  and after correction the revised bill has to be posted ebitingCrediting 4000  Maintenance Charges  and debiting   1100	Maintenance Dues Receivablew ith proper Flat ID and Members due register has to be updated properly with the revised bill so that it it shows corrected/revised amount due



Reason for Change

added revised Fixed expenses calculation method and individual bill reversal system

☐ Bug/Error correction

☐ Security vulnerability

☐ Performance issue

☑ Regulatory compliance

☑ Business requirement change

☐ Technology upgrade

☑ Data integrity issue



Without this engine, the society cannot legally or fairly collect maintenance.



Urgency Level



Critical — This is core functionality. Without it, the society cannot operate.



2\. IMPACT ANALYSIS

2.1 Business Impact



Positive Effects



Legally valid billing



Transparent dues for members



Accurate society income tracking



Reduced disputes



Negative Effects



Initial setup complexity



Requires correct master data (sq.ft, inmates)



Business Metrics Affected



Revenue impact: Enables 100% of society collections



Cost impact: Low



Productivity impact: Huge improvement for treasurer \& committee



2.2 Technical Impact



Systems Affected



☑ Frontend UI



☑ Backend API



☑ Database



☑ Reports



☑ Documentation



Dependencies



Flat master (sq.ft)



Inmates (headcount)



Billing rules



Monthly expenses



Performance Impact



Minor increase in computation during bill generation



No real-time performance risk



2.3 User Impact



Users Affected



All flat owners and tenants



Treasurer and committee



Workflow Changes



Members receive system-generated monthly bills



Payments link to bills



Dues auto-calculated



Training Required



Short onboarding for treasurer



Communication Plan



In-app notification



Email of first bill



#### 3\. DETAILED REQUIREMENTS



3.1 Functional Changes



FC-1: Maintenance Calculation



Input: Flat sq.ft, maintenance rate



Process: sq.ft × rate



Output: Monthly maintenance



FC-2: Water Calculation



Input: Total water bill, inmate count



Process: Total ÷ total inmates × flat inmates



Output: Flat water charge



FC-3: Fixed Expenses

total of selective expenses ÷ total flat or ÷ total area  x individual flat

Output: Flat Fixed expenses


Repair fund = per flat or per sq. ft. as per Input

Sinking Fund =Sinking fund per sq.ft or per flat as per Input

Corpus fund= per flat or per sq. ft. as per Input





FC-4: Bill Generation



Create bill for every flat



Post ledger entries



Set due date



3.2 Non-Functional Chan


Performance



Bill generation for 50–500 flats must complete < 5 seconds



Security



Bills cannot be edited after posting but admin has the right reverse the entire bill and regenerate with proper notes /committee approval for reversal and regeneration.

Only committee can regenerate

Once a bill generated for a month again cannot be re generated if it is not reversed.



Usability



Members must see breakup clearly



Treasurer can export reports



#### 4\. IMPLEMENTATION DETAILS



Modules to Modify



billing\_engine



flat\_master



inmate\_module



ledger



reports



New Components



Monthly billing engine



Rate master



Bill generator



Member ledger



Database Changes



bills



billing\_rules



monthly\_expenses



ledger\_entries



(Already defined in GharMitra architecture)



#### 5\. TESTING REQUIREMENTS

5.1 Test Strategy



Unit test: calculations



Integration test: ledger posting



System test: full billing cycle



5.2 Test Cases



1200 sq.ft flat



900 sq.ft flat



Different inmate counts



Late payment scenario



#### 6\. RISK ASSESSMENT



Risk	Impact	Probability	Mitigation

Wrong charges	High	Medium	Formula-based engine

Data errors	High	Medium	Validation

Disputes	Medium	Medium	Dispute module



#### 7\. IMPLEMENTATION PLAN



Phase 1 – Design

Phase 2 – Engine

Phase 3 – Testing

Phase 4 – Live billing



#### 8\. ROLLBACK PLAN



If billing errors:



Revert bills



Recalculate



Notify members



#### 9\. SUCCESS CRITERIA



All flats receive bills



Ledger balances match



Auditor accepts statements



#### 10\. APPROVALS



Product Owner ✔

Secretary ✔

Treasurer ✔

