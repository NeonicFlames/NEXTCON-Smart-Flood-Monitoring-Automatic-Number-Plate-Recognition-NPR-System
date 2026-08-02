"use client";

import { useEffect, useState } from "react";
import PageHeader from "@/components/PageHeader";
import { Waves, AlertTriangle, ShieldAlert, Activity } from "lucide-react";
import { getLatestReading, subscribeToFloodReadings } from "@/lib/queries/flood";
import { getSettings } from "@/lib/queries/settings";

interface FloodReading {
  depth_cm: number;
  status: string;
}

export default function Flood() {
  const [reading, setReading] = useState<FloodReading | null>(null);
  const [warningThreshold, setWarningThreshold] = useState(25);
  const [dangerThreshold, setDangerThreshold] = useState(40);

  useEffect(() => {
    async function load() {
      try {
        const [r, s] = await Promise.all([getLatestReading(), getSettings()]);
        setReading(r);
        if (s.warning_threshold_cm) setWarningThreshold(parseFloat(s.warning_threshold_cm));
        if (s.danger_threshold_cm) setDangerThreshold(parseFloat(s.danger_threshold_cm));
      } catch (e) {
        console.error("Failed to load flood data:", e);
      }
    }
    load();

    const sub = subscribeToFloodReadings((newReading) => {
      setReading(newReading as FloodReading);
    });
    return () => { sub.unsubscribe(); };
  }, []);

  const depth = reading?.depth_cm ?? 0;
  const depthDisplay = depth.toFixed(2);
  const status = reading?.status ?? "SAFE";

  const statusColor =
    status === "DANGER"
      ? "var(--color-danger)"
      : status === "WARNING"
      ? "var(--color-warn)"
      : "var(--color-safe)";

  const statusDot =
    status === "DANGER"
      ? "status-dot--danger"
      : status === "WARNING"
      ? "status-dot--warn"
      : "status-dot--safe";

  const bannerBg =
    status === "DANGER"
      ? "var(--color-danger-subtle)"
      : status === "WARNING"
      ? "var(--color-warn-subtle)"
      : "var(--color-safe-subtle)";

  const bannerBorder =
    status === "DANGER"
      ? "#5c2226"
      : status === "WARNING"
      ? "#4d3a1a"
      : "#1d4a3a";

  const bannerLabel =
    status === "DANGER"
      ? "Critical Flood Conditions"
      : status === "WARNING"
      ? "Elevated Water Level"
      : "Normal Water Conditions";

  const bannerBadge =
    status === "DANGER"
      ? "DANGER"
      : status === "WARNING"
      ? "CAUTION"
      : "LEVEL OK";

  const bannerDescription =
    status === "DANGER"
      ? `Water level is currently ${depthDisplay} cm, exceeding the ${dangerThreshold} cm danger threshold. Immediate evacuation required for campus parking areas.`
      : status === "WARNING"
      ? `Water level is currently ${depthDisplay} cm, above the ${warningThreshold} cm warning threshold. Monitor situation closely.`
      : `Water level is currently ${depthDisplay} cm, well below the ${warningThreshold} cm alert threshold. No action required for campus parking areas.`;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <PageHeader
        icon={Waves}
        title="Flood Water Level Monitoring"
        subtitle="Ultrasonic telemetry and automated water rise detection"
        actions={
          <div
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs self-start sm:self-auto"
            style={{
              background: "var(--color-paper-2)",
              color: "var(--color-neutral)",
              border: "1px solid var(--color-rule)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            <Activity size={14} style={{ color: "var(--color-safe)" }} />
            <span>Telemetry Polling · 5s</span>
          </div>
        }
      />

      {/* Primary Telemetry Metrics */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Sensor Health
          </p>
          <p
            className="text-lg font-semibold mt-2 flex items-center gap-2"
            style={{ color: "var(--color-safe)" }}
          >
            <span className="status-dot status-dot--safe" />
            Active &amp; Calibrated
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Current Water Depth
          </p>
          <p
            className="text-2xl font-bold mt-2"
            style={{
              color: "var(--color-info)",
              fontFamily: "var(--font-outlier)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {depthDisplay} cm
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Overall Risk State
          </p>
          <p
            className="text-2xl font-bold mt-2 flex items-center gap-2"
            style={{ color: statusColor }}
          >
            <span className={`status-dot ${statusDot}`} />
            {status}
          </p>
        </div>
      </section>

      {/* Current Environmental State */}
      <section
        className="card p-6"
        style={{
          background: bannerBg,
          border: `1px solid ${bannerBorder}`,
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 rounded-full" style={{ background: statusColor }} />
            <h2
              className="text-lg font-bold"
              style={{ color: statusColor }}
            >
              {bannerLabel}
            </h2>
          </div>
          <span
            className="text-xs font-medium px-2.5 py-0.5 rounded-full"
            style={{
              background: "var(--color-paper-2)",
              color: statusColor,
              border: `1px solid ${bannerBorder}`,
              fontFamily: "var(--font-outlier)",
            }}
          >
            {bannerBadge}
          </span>
        </div>

        <p className="text-sm mt-3" style={{ color: "var(--color-ink-2)" }}>
          {bannerDescription}
        </p>
      </section>

      {/* Flood Alert Threshold Parameters */}
      <section className="card">
        <h2
          className="text-sm font-semibold mb-4"
          style={{ color: "var(--color-ink)" }}
        >
          Configured Alert Thresholds
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            className="p-5 rounded-xl"
            style={{
              background: "var(--color-warn-subtle)",
              borderLeft: "3px solid var(--color-warn)",
              border: "1px solid #4d3a1a",
            }}
          >
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} style={{ color: "var(--color-warn)" }} />
              <span className="text-xs font-semibold" style={{ color: "var(--color-warn)" }}>
                Warning Threshold
              </span>
            </div>
            <p
              className="text-2xl font-bold mt-2"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-outlier)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {warningThreshold} cm
            </p>
            <p className="text-xs mt-1" style={{ color: "var(--color-neutral)" }}>
              Triggers warning notifications to security personnel
            </p>
          </div>

          <div
            className="p-5 rounded-xl"
            style={{
              background: "var(--color-danger-subtle)",
              borderLeft: "3px solid var(--color-danger)",
              border: "1px solid #5c2226",
            }}
          >
            <div className="flex items-center gap-2">
              <ShieldAlert size={16} style={{ color: "var(--color-danger)" }} />
              <span className="text-xs font-semibold" style={{ color: "var(--color-danger)" }}>
                Danger Threshold
              </span>
            </div>
            <p
              className="text-2xl font-bold mt-2"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-outlier)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {dangerThreshold} cm
            </p>
            <p className="text-xs mt-1" style={{ color: "var(--color-neutral)" }}>
              Triggers emergency vehicle evacuation broadcast
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}