import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { depth_cm, sensor_id } = body;

    if (depth_cm === undefined) {
      return Response.json(
        { error: "depth_cm is required" },
        { status: 400 }
      );
    }

    // Get thresholds from system_settings
    const { data: settings } = await supabase
      .from("system_settings")
      .select("key, value")
      .in("key", ["warning_threshold_cm", "danger_threshold_cm"]);

    let warningThreshold = 25;
    let dangerThreshold = 40;

    for (const s of settings ?? []) {
      if (s.key === "warning_threshold_cm") warningThreshold = parseFloat(s.value);
      if (s.key === "danger_threshold_cm") dangerThreshold = parseFloat(s.value);
    }

    // Auto-calculate status
    const depth = parseFloat(depth_cm);
    let status = "SAFE";
    if (depth >= dangerThreshold) status = "DANGER";
    else if (depth >= warningThreshold) status = "WARNING";

    // Insert reading
    const { data: reading, error } = await supabase
      .from("flood_readings")
      .insert({
        depth_cm: depth,
        status,
        sensor_id: sensor_id || "SENSOR-01",
      })
      .select()
      .single();

    if (error) {
      return Response.json({ error: error.message }, { status: 500 });
    }

    return Response.json({
      reading_id: reading.id,
      depth_cm: depth,
      status,
      thresholds: { warning: warningThreshold, danger: dangerThreshold },
    });
  } catch {
    return Response.json({ error: "Invalid request body" }, { status: 400 });
  }
}
