// ─── User ────────────────────────────────────────────────────────────────

export type Madhab = "hanafi" | "shafi" | "maliki" | "hanbali" | "jafari";

export interface User {
  id: string;
  email: string;
  full_name: string;
  location_lat: number | null;
  location_lng: number | null;
  location_country: string | null;
  currency: string;
  calculation_method: number; // system-managed, never user-editable in the UI
  madhab: Madhab;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
  location_lat?: number;
  location_lng?: number;
  location_country?: string;
  currency?: string;
  madhab?: Madhab;
}

export interface UserUpdate {
  full_name?: string;
  location_lat?: number;
  location_lng?: number;
  location_country?: string;
  currency?: string;
  madhab?: Madhab;
}

// ─── Auth ────────────────────────────────────────────────────────────────

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest extends UserCreate {}

export interface RegisterResponse {
  user: User;
  tokens: AuthTokens;
}

// ─── Prayer Tracker ──────────────────────────────────────────────────────

export interface PrayerLogCreate {
  prayer_name: string;
  prayed_at: string;
  was_on_time?: boolean;
  notes?: string;
}

export interface PrayerLog {
  id: string;
  user_id: string;
  prayer_name: string;
  prayed_at: string;
  was_on_time: boolean;
  notes: string | null;
  created_at: string;
}

export interface PrayerStats {
  current_streak: number;
  longest_streak: number;
  completion_rate: number;
  total_prayers_logged: number;
}

export interface TodayPrayerStatus {
  prayer_name: string;
  completed: boolean;
  prayed_at: string | null;
}

export interface StreakResponse {
  current_streak: number;
  longest_streak: number;
}

// ─── Zakat ───────────────────────────────────────────────────────────────

export interface ZakatInput {
  cash_savings?: number;
  gold_value?: number;
  silver_value?: number;
  business_assets?: number;
}

export interface ZakatResult {
  id: string;
  total_wealth: number;
  nisab_threshold: number;
  nisab_gold: number;
  nisab_silver: number;
  is_zakat_due: boolean;
  zakat_amount: number;
  currency: string;
  calculated_at: string;
}

// ─── Chat ────────────────────────────────────────────────────────────────

// Similarity is either a numeric relevance score (knowledge base match) or
// one of two string markers indicating a direct lookup or web source.
export interface RawCitationSource {
  source_file: string;
  similarity: number | "web_source" | "direct_lookup";
}

// UI-facing shape matching the three citation chip variants: knowledge
// base, direct lookup, and web source.
export interface CitationSource {
  sourceFile: string;
  type: "knowledge_base" | "direct_lookup" | "web_source";
  similarity?: number;
}

export interface ChatMessageCreate {
  question: string;
  session_id?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  sources: RawCitationSource[] | null;
  created_at: string;
}

export interface ChatResponse {
  answer: string;
  sources: RawCitationSource[];
  tools_used: string[];
  session_id: string | null;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionListItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string | null;
}

// ─── Prayer Times ────────────────────────────────────────────────────────

export interface PrayerTimesResponse {
  date: string;
  timezone: string;
  timings: Record<string, string>;
}

export interface NextPrayerResponse {
  prayer_name: string;
  time: string;
  timezone: string;
  seconds_until: number;
}

// ─── Dua / Surah Finder ──────────────────────────────────────────────────

// Backend returns dua content verbatim — never paraphrased. content and
// metadata are passed through unmodified from duas.json.
export interface DuaResult {
  content: string;
  metadata: Record<string, unknown>;
  similarity: number | null;
}

export interface SurahResult {
  content: string;
  metadata: Record<string, unknown>;
}

export interface SurahListItem {
  number: number;
  name: string;
}