import { supabase } from "@/lib/supabase";

export async function getSettings() {
  const { data, error } = await supabase
    .from("system_settings")
    .select("*")
    .order("key");

  if (error) throw error;

  // Convert array of { key, value } into an object
  const settings: Record<string, string> = {};
  for (const row of data ?? []) {
    settings[row.key] = row.value;
  }
  return settings;
}

export async function updateSetting(key: string, value: string) {
  const { error } = await supabase
    .from("system_settings")
    .update({ value, updated_at: new Date().toISOString() })
    .eq("key", key);

  if (error) throw error;
}

export async function getCameras() {
  const { data, error } = await supabase
    .from("cameras")
    .select("*")
    .order("name");

  if (error) throw error;
  return data;
}
