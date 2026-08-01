import { supabase } from "@/lib/supabase";

export async function getRecentDetections(limit = 10) {
  const { data, error } = await supabase
    .from("plate_detections")
    .select("*, registered_vehicles(owner_name, phone, zone)")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return data;
}

export async function getTodayCount() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const { count, error } = await supabase
    .from("plate_detections")
    .select("*", { count: "exact", head: true })
    .gte("created_at", today.toISOString());

  if (error) throw error;
  return count ?? 0;
}

export async function getRegisteredVehicles() {
  const { data, error } = await supabase
    .from("registered_vehicles")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) throw error;
  return data;
}

export function subscribeToDetections(
  callback: (payload: unknown) => void
) {
  const channel = supabase
    .channel(`plate_detections_${Math.random().toString(36).substring(2, 9)}`)
    .on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "plate_detections" },
      (payload) => callback(payload.new)
    );

  channel.subscribe();

  return {
    unsubscribe: () => {
      supabase.removeChannel(channel);
    },
  };
}
