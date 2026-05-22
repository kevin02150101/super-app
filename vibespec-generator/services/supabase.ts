import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { TechSpec } from '../types';

// Read Vite env vars. Keys with the VITE_ prefix get baked into the client bundle —
// only put the *publishable* / *anon* key here. Never the service_role key.
const URL = (import.meta as any).env?.VITE_SUPABASE_URL as string | undefined;
const KEY = (import.meta as any).env?.VITE_SUPABASE_ANON_KEY as string | undefined;

export const SUPA_ENABLED = !!(URL && KEY);

let _client: SupabaseClient | null = null;
function client(): SupabaseClient | null {
  if (!SUPA_ENABLED) return null;
  if (!_client) _client = createClient(URL!, KEY!);
  return _client;
}

// Per-browser identifier so anonymous users only see their own specs.
function deviceId(): string {
  const key = 'vibe-device-id';
  let id = localStorage.getItem(key);
  if (!id) {
    id = (crypto?.randomUUID?.() ?? `dev_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    localStorage.setItem(key, id);
  }
  return id;
}

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
  const row = {
    device_id: deviceId(),
    name: (name || 'Untitled').slice(0, 120),
    spec,
    refined_markdown: refinedMarkdown,
  };
  const { data, error } = await sb.from('vibespecs').insert(row).select().single();
  if (error) { console.error('saveSpec error', error); return null; }
  return data as SavedSpec;
}

export async function listSpecs(limit = 10): Promise<SavedSpec[]> {
  const sb = client();
  if (!sb) return [];
  const { data, error } = await sb
    .from('vibespecs')
    .select('id, name, spec, refined_markdown, created_at')
    .eq('device_id', deviceId())
    .order('created_at', { ascending: false })
    .limit(limit);
  if (error) { console.error('listSpecs error', error); return []; }
  return (data || []) as SavedSpec[];
}

export async function deleteSpec(id: string): Promise<boolean> {
  const sb = client();
  if (!sb) return false;
  const { error } = await sb.from('vibespecs').delete().eq('id', id).eq('device_id', deviceId());
  return !error;
}
