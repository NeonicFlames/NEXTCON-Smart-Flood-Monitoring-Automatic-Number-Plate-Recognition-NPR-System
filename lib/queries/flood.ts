import { supabase } from "@/lib/supabase";

export async function getLatestReading() {
  const { data, error } = await supabase
    .from("flood_readings")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(1)
    .single();

  if (error) throw error;
  return data;
}

export async function getReadingHistory(limit = 10) {
  const { data, error } = await supabase
    .from("flood_readings")
    .select("*")
    .order("created_at", { ascending: true })
    .limit(limit);

  if (error) throw error;
  return data;
}

export function subscribeToFloodReadings(
  callback: (payload: unknown) => void
) {
  const channel = supabase
    .channel(`flood_readings_${Math.random().toString(36).substring(2, 9)}`)
    .on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "flood_readings" },
      (payload) => callback(payload.new)
    );

  channel.subscribe();

  return {
    unsubscribe: () => {
      supabase.removeChannel(channel);
    },
  };
}
