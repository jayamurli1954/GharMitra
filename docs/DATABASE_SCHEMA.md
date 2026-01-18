## Flats ##

flats (
  flat_id PK,
  society_id,
  flat_no,
  status
)

## Persons ##

ppersons (
  person_id PK,
  name,
  phone,
  email
)

## Occupancy History ##

flat_occupancy (
  occupancy_id PK,
  flat_id,
  person_id,
  role ENUM('OWNER','TENANT'),
  start_date,
  end_date,
  verified_by,
  verification_date
)


## Document Verification (No uploads) ##

document_verification (
  verification_id PK,
  flat_id,
  person_id,
  sale_deed_verified BOOLEAN,
  rent_agreement_verified BOOLEAN,
  police_verification BOOLEAN,
  verified_by,
  verified_date
)

## No-Dues Certificate ##

no_dues_certificate (
  ndc_id PK,
  flat_id,
  issued_date,
  issued_by,
  purpose,
  balance_at_issue,
  is_valid BOOLEAN
)


## Enforcement Rule ##

IF flat.balance > 0
THEN ownership_transfer = BLOCKED
