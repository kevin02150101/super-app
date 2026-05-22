import { createClient, type SupabaseClient, type User } from '@supabase/supabase-js';
import type { TechSpec } from '../types';

// Read Vite env vars. Keys with the VITE_ prefix get baked into the client bundle —
// only put the *publishable* / *anon* key here. Never the service_role key.
const URL = (import.meta as any).env?.VITE_SUPABASE_URL as string | undefined;
const KEY = (import.meta as any).env?.VITE_SUPABASE_ANON_KEY as string | undefined;

export const SUPA_ENABLED = !!(URL && KEY);

let _client: SupabaseClient | null = null;
export function client(): SupabaseClient | null {
  if (!SUPA_ENABLED) return null;
  if (!_client) _client = createClient(URL!, KEY!, {
    auth: { persistSession: true, autoRefreshToken: true, storageKey: 'vibe-auth' },
  });
  return _client;
}

// Per-browser identifier — used when the user has not signed in.
function deviceId(): string {
  const key = 'vibe-device-id';
  let id = localStorage.getItem(key);
  if (!id) {
    id = (crypto?.randomUUID?.() ?? `dev_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    localStorage.setItem(key, id);
  }
  return id;
}

// ----- AUTH -----
export type AuthUser = { id: string; email: string | null };

function toAuth(u: User | null): AuthUser | null {
  if (!u) return null;
  return { id: u.id, email: u.email ?? null };
}

export async function getUser(): Promise<AuthUser | null> {
  const sb = client();
  if (!sb) return null;
  const { data } = await sb.auth.getUser();
  return toAuth(data.user);
}

export function onAuthChange(cb: (u: AuthUser | null) => void): () => void {
  const sb = client();
  if (!sb) return () => {};
  const { data } = sb.auth.onAuthStateChange((_e, session) => cb(toAuth(session?.user ?? null)));
  return () => data.subscription.unsubscribe();
}

export async function signUp(email: string, password: string): Promise<{ ok: boolean; error?: string; needsConfirm?: boolean }> {
  const sb = client();
  if (!sb) return { ok: false, error: 'Supabase not configured' };
  const { data, error } = await sb.auth.signUp({ email, password });
  if (error) return { ok: false, error: error.message };
  // If email-confirmation is on, session will be null until the user clicks the email.
  return { ok: true, needsConfirm: !data.session };
}

export async function signIn(email: string, password: string): Promise<{ ok: boolean; error?: string }> {
  const sb = client();
  if (!sb) return { ok: false, error: 'Supabase not configured' };
  const { error } = await sb.auth.signInWithPassword({ email, password });
  if (error) return { ok: false, error: error.message };
  return { ok: true };
}

export async function signOut(): Promise<void> {
  const sb = client();
  if (!sb) return;
  await sb.auth.signOut();
}

// ----- SPECS -----
export type SavedSpec = {
  id: string;
  name: string;
  spec: TechSpec;
  refined_markdown: string | null;
  created_at: string;
};

export async function saveSpec(
  name: string,
  spec: TechSpec,
  refinedMarkdown: string | null,
): Promise<SavedSpec | null> {
  const sb = client();
  if (!sb) return null;
  const user = (await sb.auth.getUser()).data.user;
  const row: Record<string, unknown> = {
    name: (name || 'Untitled').slice(0, 120),
    spec,
    refined_markdown: refinedMarkdown,
  };
  if (user) row.user_id = user.id;
  else row.device_id = deviceId();
  const { data, error } = await sb.from('vibespecs').insert(row).select().single();
  if (error) { console.error('saveSpec error', error); return null; }
  return data as SavedSpec;
}

export async function listSpecs(limit = 10): Promise<SavedSpec[]> {
  const sb = client();
  if (!sb) return [];
  const user = (await sb.auth.getUser()).data.user;
  let q = sb.from('vibespecs')
    .select('id, name, spec, refined_markdown, created_at')
    .order('created_at', { ascending: false })
    .limit(limit);
  q = user ? q.eq('user_id', user.id) : q.eq('device_id', deviceId());
  const { data, error } = await q;
  if (error) { console.error('listSpecs error', error); return []; }
  return (data || []) as SavedSpec[];
}

export async function deleteSpec(id: string): Promise<boolean> {
  const sb = client();
  if (!sb) return false;
  const { error } = await sb.from('vibespecs').delete().eq('id', id);
  return !error;
}

// Link existing device-id rows to the user that just signed in.
export async function claimDeviceSpecs(): Promise<number> {
  const sb = client();
  if (!sb) return 0;
  const user = (await sb.auth.getUser()).data.user;
  if (!user) return 0;
  const { data, error } = await sb.from('vibespecs')
    .update({ user_id: user.id })
    .is('user_id', null)
    .eq('device_id', deviceId())
    .select('id');
  if (error) { console.error('claimDeviceSpecs error', error); return 0; }
  return (data || []).length;
}
