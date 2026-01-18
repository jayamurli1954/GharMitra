-- Performance Optimization: Database Indexes for GharMitra
-- This script adds indexes for frequently queried columns to improve performance

-- Users table indexes (already has some, adding missing ones)
CREATE INDEX IF NOT EXISTS idx_users_society_role ON users(society_id, role);
CREATE INDEX IF NOT EXISTS idx_users_email_society ON users(email, society_id);
CREATE INDEX IF NOT EXISTS idx_users_apartment_society ON users(apartment_number, society_id);

-- Flats table indexes (already has some, adding compound indexes)
CREATE INDEX IF NOT EXISTS idx_flats_society_status ON flats(society_id, occupancy_status);
CREATE INDEX IF NOT EXISTS idx_flats_society_area ON flats(society_id, area_sqft);

-- Transactions table indexes (critical for performance)
CREATE INDEX IF NOT EXISTS idx_transactions_society_date ON transactions(society_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_society_type ON transactions(society_id, type);
CREATE INDEX IF NOT EXISTS idx_transactions_society_category ON transactions(society_id, category);
CREATE INDEX IF NOT EXISTS idx_transactions_society_account ON transactions(society_id, account_code);
CREATE INDEX IF NOT EXISTS idx_transactions_added_by_date ON transactions(added_by, date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_flat_id ON transactions(flat_id) WHERE flat_id IS NOT NULL;

-- Maintenance Bills table indexes (critical for billing queries)
CREATE INDEX IF NOT EXISTS idx_maintenance_bills_society_flat ON maintenance_bills(society_id, flat_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_bills_society_month_year ON maintenance_bills(society_id, year, month);
CREATE INDEX IF NOT EXISTS idx_maintenance_bills_flat_month_year ON maintenance_bills(flat_id, year, month);
CREATE INDEX IF NOT EXISTS idx_maintenance_bills_society_status ON maintenance_bills(society_id, status);

-- Account Codes table indexes
CREATE INDEX IF NOT EXISTS idx_account_codes_society_type ON account_codes(society_id, type);
CREATE INDEX IF NOT EXISTS idx_account_codes_society_code ON account_codes(society_id, code);

-- Journal Entries table indexes
CREATE INDEX IF NOT EXISTS idx_journal_entries_society_date ON journal_entries(society_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_journal_entries_society_type ON journal_entries(society_id, voucher_type);

-- Members table indexes (critical for member management)
CREATE INDEX IF NOT EXISTS idx_members_society_flat ON members(society_id, flat_id);
CREATE INDEX IF NOT EXISTS idx_members_society_status ON members(society_id, status);
CREATE INDEX IF NOT EXISTS idx_members_phone_society ON members(phone_number, society_id);
CREATE INDEX IF NOT EXISTS idx_members_email_society ON members(email, society_id);
CREATE INDEX IF NOT EXISTS idx_members_move_in_date ON members(move_in_date);
CREATE INDEX IF NOT EXISTS idx_members_move_out_date ON members(move_out_date) WHERE move_out_date IS NOT NULL;

-- Messages table indexes (for chat performance)
CREATE INDEX IF NOT EXISTS idx_messages_room_created ON messages(room_id, created_at DESC);

-- Chat Rooms table indexes
CREATE INDEX IF NOT EXISTS idx_chat_rooms_society_type ON chat_rooms(society_id, type);

-- Audit Logs table indexes (for compliance and reporting)
CREATE INDEX IF NOT EXISTS idx_audit_logs_society_action ON audit_logs(society_id, action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Complaints table indexes
CREATE INDEX IF NOT EXISTS idx_complaints_society_status ON complaints(society_id, status);
CREATE INDEX IF NOT EXISTS idx_complaints_society_priority ON complaints(society_id, priority);
CREATE INDEX IF NOT EXISTS idx_complaints_user_created ON complaints(user_id, created_at DESC);

-- Meetings table indexes
CREATE INDEX IF NOT EXISTS idx_meetings_society_date ON meetings(society_id, meeting_date DESC);
CREATE INDEX IF NOT EXISTS idx_meetings_society_status ON meetings(society_id, status);
CREATE INDEX IF NOT EXISTS idx_meetings_society_type ON meetings(society_id, meeting_type);

-- Meeting Attendance table indexes
CREATE INDEX IF NOT EXISTS idx_meeting_attendance_meeting_member ON meeting_attendance(meeting_id, member_id);

-- Meeting Resolutions table indexes
CREATE INDEX IF NOT EXISTS idx_meeting_resolutions_meeting_status ON meeting_resolutions(meeting_id, result);

-- Move-out Requests table indexes
CREATE INDEX IF NOT EXISTS idx_moveout_requests_society_status ON moveout_requests(society_id, status);
CREATE INDEX IF NOT EXISTS idx_moveout_requests_member_flat ON moveout_requests(member_id, flat_id);

-- Document Templates table indexes
CREATE INDEX IF NOT EXISTS idx_document_templates_society_category ON document_templates(society_id, category);
CREATE INDEX IF NOT EXISTS idx_document_templates_society_active ON document_templates(society_id, is_active);

-- Template Usage Logs table indexes
CREATE INDEX IF NOT EXISTS idx_template_usage_log_template_date ON template_usage_log(template_id, generated_at DESC);

-- Vendors table indexes
CREATE INDEX IF NOT EXISTS idx_vendors_society_name ON vendors(society_id, name);

-- Assets table indexes
CREATE INDEX IF NOT EXISTS idx_assets_society_category ON assets(society_id, category);
CREATE INDEX IF NOT EXISTS idx_assets_society_status ON assets(society_id, status);

-- Voucher Attachments table indexes
CREATE INDEX IF NOT EXISTS idx_voucher_attachments_journal_created ON voucher_attachments(journal_entry_id, created_at DESC);

-- Supplementary Bills table indexes
CREATE INDEX IF NOT EXISTS idx_supplementary_bills_society_date ON supplementary_bills(society_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_supplementary_bills_society_status ON supplementary_bills(society_id, status);

-- Supplementary Bill Flats table indexes
CREATE INDEX IF NOT EXISTS idx_supplementary_bill_flats_bill_flat ON supplementary_bill_flats(supplementary_bill_id, flat_id);

-- Water Expenses table indexes
CREATE INDEX IF NOT EXISTS idx_water_expenses_society_month_year ON water_expenses(society_id, year, month);

-- Fixed Expenses table indexes
CREATE INDEX IF NOT EXISTS idx_fixed_expenses_society_name ON fixed_expenses(society_id, name);

-- Apartment Settings table indexes
CREATE INDEX IF NOT EXISTS idx_apartment_settings_society_name ON apartment_settings(society_id, apartment_name);

-- NOC Documents table indexes
CREATE INDEX IF NOT EXISTS idx_noc_documents_society_flat ON noc_documents(society_id, flat_id);
CREATE INDEX IF NOT EXISTS idx_noc_documents_society_status ON noc_documents(society_id, status);

-- NOC Generation Logs table indexes
CREATE INDEX IF NOT EXISTS idx_noc_generation_log_request_date ON noc_generation_log(moveout_request_id, generated_date DESC);

-- Members Archive table indexes
CREATE INDEX IF NOT EXISTS idx_members_archive_society_date ON members_archive(society_id, archived_date DESC);
CREATE INDEX IF NOT EXISTS idx_members_archive_original_member ON members_archive(original_member_id);

-- Personal Arrears table indexes
CREATE INDEX IF NOT EXISTS idx_personal_arrears_member_flat ON personal_arrears(member_id, flat_id);
CREATE INDEX IF NOT EXISTS idx_personal_arrears_society_status ON personal_arrears(society_id, status);

-- Opening Balances table indexes (if exists)
-- CREATE INDEX IF NOT EXISTS idx_opening_balances_account_year ON opening_balances(account_code_id, financial_year_id);

-- Financial Years table indexes (if exists)
-- CREATE INDEX IF NOT EXISTS idx_financial_years_society_status ON financial_years(society_id, status);

-- Online Payments table indexes (if exists)
-- CREATE INDEX IF NOT EXISTS idx_online_payments_society_status ON online_payments(society_id, status);

-- Payments table indexes (if exists)
-- CREATE INDEX IF NOT EXISTS idx_payments_bill_date ON payments(bill_id, payment_date DESC);