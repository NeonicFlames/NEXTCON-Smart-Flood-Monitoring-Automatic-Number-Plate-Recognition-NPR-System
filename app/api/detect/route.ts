import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { plate_number, confidence, camera_id, image_url } = body;

    if (!plate_number || confidence === undefined) {
      return Response.json(
        { error: "plate_number and confidence are required" },
        { status: 400 }
      );
    }

    // 1. Check if plate is registered
    const { data: vehicle } = await supabase
      .from("registered_vehicles")
      .select("id, owner_name, zone")
      .eq("plate_number", plate_number.toUpperCase())
      .eq("is_active", true)
      .single();

    const is_registered = !!vehicle;

    // 2. Insert detection
    const { data: detection, error: detectionError } = await supabase
      .from("plate_detections")
      .insert({
        plate_number: plate_number.toUpperCase(),
        confidence: parseFloat(confidence),
        camera_id: camera_id || null,
        vehicle_id: vehicle?.id || null,
        is_registered,
        image_url: image_url || null,
      })
      .select()
      .single();

    if (detectionError) {
      return Response.json({ error: detectionError.message }, { status: 500 });
    }

    // 3. If registered + active flood → create alert
    let alert_created = false;
    if (is_registered) {
      // Get latest flood reading
      const { data: latestReading } = await supabase
        .from("flood_readings")
        .select("id, depth_cm, status")
        .order("created_at", { ascending: false })
        .limit(1)
        .single();

      if (
        latestReading &&
        (latestReading.status === "WARNING" || latestReading.status === "DANGER")
      ) {
        const { error: alertError } = await supabase
          .from("flood_alerts")
          .insert({
            vehicle_id: vehicle.id,
            plate_number: plate_number.toUpperCase(),
            flood_reading_id: latestReading.id,
            flood_level_cm: latestReading.depth_cm,
            alert_type: latestReading.status,
            message: `${latestReading.status} alert: Vehicle ${plate_number.toUpperCase()} (${vehicle.owner_name}) detected in ${vehicle.zone} during flood level ${latestReading.depth_cm}cm`,
            is_notified: true,
            is_acknowledged: false,
          });

        if (!alertError) alert_created = true;
      }
    }

    return Response.json({
      detection_id: detection.id,
      is_registered,
      vehicle_id: vehicle?.id || null,
      alert_created,
    });
  } catch {
    return Response.json({ error: "Invalid request body" }, { status: 400 });
  }
}
