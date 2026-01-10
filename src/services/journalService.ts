/**
 * Journal Entry Service
 * Handles double-entry bookkeeping journal entries
 */
import api from './api';

export interface JournalEntryLine {
  account_code: string;
  debit_amount: number;
  credit_amount: number;
  description?: string;
}

export interface JournalEntryCreate {
  date: string;
  description: string;
  entries: JournalEntryLine[];
}

export interface JournalEntry {
  id: string;
  entry_number: string;
  date: string;
  description: string;
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
  added_by: string;
  created_at: string;
  updated_at: string;
  entries: Array<{
    id: string;
    account_code: string;
    debit_amount: number;
    credit_amount: number;
    description: string;
  }>;
}

export const journalService = {
  async createJournalEntry(data: JournalEntryCreate): Promise<JournalEntry> {
    const response = await api.post<JournalEntry>('/journal/', data);
    return response.data;
  },

  async getJournalEntries(
    from_date?: string,
    to_date?: string
  ): Promise<JournalEntry[]> {
    const params: any = {};
    if (from_date) params.from_date = from_date;
    if (to_date) params.to_date = to_date;

    const response = await api.get<JournalEntry[]>('/journal/', { params });
    return response.data;
  },

  async getJournalEntry(entryId: string): Promise<JournalEntry> {
    const response = await api.get<JournalEntry>(`/journal/${entryId}`);
    return response.data;
  },
};








