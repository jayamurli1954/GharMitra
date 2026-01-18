Database Permission Model

These tables enforce finance security at database & API level.

1. roles

CREATE TABLE roles (
  role_id INT PRIMARY KEY,
  role_code VARCHAR(10) UNIQUE,
  role_name VARCHAR(50)
);


2. user_roles

CREATE TABLE user_roles (
  user_id INT,
  society_id INT,
  role_id INT,
  PRIMARY KEY (user_id, society_id)
);


3. permissions

CREATE TABLE permissions (
  permission_id INT PRIMARY KEY,
  permission_code VARCHAR(50),
  description TEXT
);



Examples:

VIEW_OWN_LEDGER
VIEW_SOCIETY_SUMMARY
VIEW_MEMBER_DUES
VIEW_BANK_LEDGER
VIEW_VENDOR_PAYMENTS
VIEW_AUDIT_REPORTS



4. role_permissions

CREATE TABLE role_permissions (
  role_id INT,
  permission_id INT,
  PRIMARY KEY (role_id, permission_id)
);



5. audit_log


CREATE TABLE audit_log (
  log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id INT,
  society_id INT,
  action VARCHAR(100),
  entity_type VARCHAR(50),
  entity_id INT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


🛡 Enforcement Logic (API)
if user.role == 'MEM':
   data = query where flat_id = user.flat_id

if user.role in ('ADM','COM','AUD'):
   data = query where society_id = user.society_id



🏆 Result

With this:

. Members can never spy on others

. Committee has full control

. Auditors get clean books

. GharMitra becomes AGM-ready, audit-ready, and legally safe
