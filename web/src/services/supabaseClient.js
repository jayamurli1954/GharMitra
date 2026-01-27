/**
 * Supabase client (web)
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl =
  (typeof process !== 'undefined' &&
    process.env &&
    process.env.REACT_APP_SUPABASE_URL) ||
  (typeof window !== 'undefined' && window.__SUPABASE_URL__);
const supabaseAnonKey =
  (typeof process !== 'undefined' &&
    process.env &&
    process.env.REACT_APP_SUPABASE_ANON_KEY) ||
  (typeof window !== 'undefined' && window.__SUPABASE_ANON_KEY__);

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase env vars missing: REACT_APP_SUPABASE_URL / REACT_APP_SUPABASE_ANON_KEY');
}

export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '', {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

export default supabase;
