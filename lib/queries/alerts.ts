import { supabase } from "@/lib/supabase";

export async function getActiveFloodAlerts() {
  const { data, error } = await supabase
    .from("flood_alerts")
    .select("*, registered_vehicles(owner_name, phone, email, zone)")
    .eq("is_acknowledged", false)
    .order("created_at", { ascending: false });

  if (error) throw error;
  return data;
}

export async function getAlertHistory(limit = 20) {
  const { data, error } = await supabase
    .from("flood_alerts")
    .select("*, registered_vehicles(owner_name, phone, zone)")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) throw error;
  return data;
}

export async function acknowledgeAlert(alertId: string) {
  const { error } = await supabase
    .from("flood_alerts")
    .update({ is_acknowledged: true })
    .eq("id", alertId);

  if (error) throw error;
}

export function subscribeToAlerts(
  callback: (payload: unknown) => void
) {
  const channel = supabase
    .channel(`flood_alerts_${Math.random().toString(36).substring(2, 9)}`)
    .on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "flood_alerts" },
      (payload) => callback(payload.new)
    );

  channel.subscribe();

  return {
    unsubscribe: () => {
      supabase.removeChannel(channel);
    },
  };
}
