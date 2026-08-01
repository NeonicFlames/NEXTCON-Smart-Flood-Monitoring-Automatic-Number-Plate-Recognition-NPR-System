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

export interface NewVehicleInput {
  plate_number: string;
  owner_name: string;
  phone?: string;
  email?: string;
  vehicle_type?: string;
  zone?: string;
  is_active?: boolean;
}

export async function addRegisteredVehicle(vehicle: NewVehicleInput) {
  const formattedPlate = vehicle.plate_number.trim().toUpperCase();
  const { data, error } = await supabase
    .from("registered_vehicles")
    .insert([
      {
        plate_number: formattedPlate,
        owner_name: vehicle.owner_name.trim(),
        phone: vehicle.phone?.trim() || null,
        email: vehicle.email?.trim() || null,
        vehicle_type: vehicle.vehicle_type || "Car",
        zone: vehicle.zone || "Zone A",
        is_active: vehicle.is_active ?? true,
      },
    ])
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function deleteRegisteredVehicle(id: string) {
  const { error } = await supabase
    .from("registered_vehicles")
    .delete()
    .eq("id", id);

  if (error) throw error;
  return true;
}

export async function toggleRegisteredVehicleStatus(id: string, is_active: boolean) {
  const { data, error } = await supabase
    .from("registered_vehicles")
    .update({ is_active })
    .eq("id", id)
    .select()
    .single();

  if (error) throw error;
  return data;
}

export async function checkVehiclePermit(plateNumber: string) {
  const cleanPlate = plateNumber.trim().toUpperCase();
  const { data, error } = await supabase
    .from("registered_vehicles")
    .select("*")
    .ilike("plate_number", cleanPlate)
    .maybeSingle();

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

