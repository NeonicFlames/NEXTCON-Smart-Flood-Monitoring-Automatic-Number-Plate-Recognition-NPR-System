"use client";

import { useEffect, useState } from "react";
import WaterChart from "@/components/WaterChart";
import { LayoutDashboard, Camera, ShieldCheck } from "lucide-react";
import { getLatestReading } from "@/lib/queries/flood";
import { getRecentDetections, getTodayCount } from "@/lib/queries/vehicles";
import { subscribeToFloodReadings } from "@/lib/queries/flood";
import { subscribeToDetections } from "@/lib/queries/vehicles";

interface FloodReading {
  depth_cm: number;
  status: string;
}

interface Detection {
  id: string;
  plate_number: string;
  confidence: number;
  is_registered: boolean;
  created_at: string;
}

export default function Home() {
  const [reading, setReading] = useState<FloodReading | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [todayCount, setTodayCount] = useState(0);
  const [updatedAgo, setUpdatedAgo] = useState("—");

  useEffect(() => {
    async function load() {
      try {
        const [r, d, c] = await Promise.all([
          getLatestReading(),
          getRecentDetections(5),
          getTodayCount(),
        ]);
        setReading(r);
        setDetections(d as Detection[]);
        setTodayCount(c);
        setUpdatedAgo("just now");
      } catch (e) {
        console.error("Failed to load dashboard data:", e);
      }
    }
    load();

    const floodSub = subscribeToFloodReadings((newReading) => {
      setReading(newReading as FloodReading);
      setUpdatedAgo("just now");
    });
    const detSub = subscribeToDetections((newDetection) => {
      setDetections((prev) => [newDetection as Detection, ...prev.slice(0, 4)]);
      setTodayCount((c) => c + 1);
      setUpdatedAgo("just now");
    });

    return () => {
      floodSub.unsubscribe();
      detSub.unsubscribe();
    };
  }, []);

  const statusColor =
    reading?.status === "DANGER"
      ? "var(--color-danger)"
      : reading?.status === "WARNING"
        ? "var(--color-warn)"
        : "var(--color-safe)";

  const statusDot =
    reading?.status === "DANGER"
      ? "status-dot--danger"
      : reading?.status === "WARNING"
        ? "status-dot--warn"
        : "status-dot--safe";

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div
            className="p-2.5 rounded-lg shrink-0"
            style={{
              background: "var(--color-paper-2)",
              color: "var(--color-accent)",
              border: "1px solid var(--color-rule)",
            }}
          >
            <LayoutDashboard size={22} />
          </div>
          <div>
            <h1
              className="font-display font-bold text-xl tracking-tight"
              style={{
                color: "var(--color-ink)",
              }}
            >
              Smart Flood &amp; Vehicle Telemetry
            </h1>
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Real-time environmental monitoring &amp; automatic plate recognition
            </p>
          </div>
        </div>

      </div>

      {/* Primary Metrics */}
      <section className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card col-span-2 lg:col-span-1">
          <p className="text-category">
            System Status
          </p>
          <p
            className="text-lg font-display font-semibold mt-1 flex items-center gap-2"
            style={{ color: "var(--color-safe)" }}
          >
            <span className="status-dot status-dot--safe" />
            Online
          </p>
        </div>

        <div className="card">
          <p className="text-category">
            Flood Condition
          </p>
          <p
            className="text-2xl font-display font-bold mt-1 flex items-center gap-2"
            style={{ color: statusColor }}
          >
            <span className={`status-dot ${statusDot}`} />
            {reading?.status ?? "—"}
          </p>
        </div>

        <div className="card">
          <p className="text-category">
            Water Depth
          </p>
          <p
            className="text-2xl font-outlier font-bold mt-1"
            style={{
              color: "var(--color-info)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {reading ? `${reading.depth_cm} cm` : "—"}
          </p>
        </div>

        <div className="card">
          <p className="text-category">
            Detections Today
          </p>
          <p
            className="text-2xl font-outlier font-bold mt-1"
            style={{
              color: "var(--color-ink)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {todayCount}
          </p>
        </div>

        <div className="card">
          <p className="text-category">
            Latest Detection
          </p>
          <p
            className="text-2xl plate-number mt-1"
            style={{
              color: "var(--color-accent)",
            }}
          >
            {detections[0]?.plate_number ?? "—"}
          </p>
        </div>
      </section>

      {/* Vehicle Recognition Activity Table */}
      <section className="card-flush">
        <div className="px-5 pt-5 pb-3 flex items-center justify-between">
          <h2
            className="font-display font-semibold text-base"
            style={{ color: "var(--color-ink)" }}
          >
            Recent Vehicle Detections
          </h2>
          <span
            className="text-xs font-outlier"
            style={{
              color: "var(--color-muted)",
            }}
          >
            Updated {updatedAgo}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--color-rule)" }}>
                <th
                  className="text-left px-5 py-2.5 text-category"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Plate Number
                </th>
                <th
                  className="text-left px-5 py-2.5 text-category"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Time
                </th>
                <th
                  className="text-left px-5 py-2.5 text-category"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Confidence
                </th>
                <th
                  className="text-left px-5 py-2.5 text-category"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {detections.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-5 py-6 text-center text-sm" style={{ color: "var(--color-muted)" }}>
                    No detections yet
                  </td>
                </tr>
              )}
              {detections.map((d, i) => (
                <tr
                  key={d.id ?? i}
                  style={{
                    borderBottom:
                      i < detections.length - 1
                        ? "1px solid var(--color-rule)"
                        : "none",
                  }}
                >
                  <td
                    className="px-5 py-3 plate-number"
                    style={{
                      color: "var(--color-accent)",
                    }}
                  >
                    {d.plate_number}
                  </td>
                  <td
                    className="px-5 py-3 font-outlier"
                    style={{
                      color: "var(--color-ink-2)",
                    }}
                  >
                    {new Date(d.created_at).toLocaleTimeString([], {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </td>
                  <td
                    className="px-5 py-3 font-outlier font-medium"
                    style={{
                      color: "var(--color-safe)",
                    }}
                  >
                    {Math.round(d.confidence * 100)}%
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 text-xs font-outlier font-medium px-2.5 py-0.5 rounded-full"
                      style={{
                        background: d.is_registered
                          ? "var(--color-safe-subtle)"
                          : "var(--color-warn-subtle)",
                        color: d.is_registered
                          ? "var(--color-safe)"
                          : "var(--color-warn)",
                        border: `1px solid ${d.is_registered
                          ? "oklch(70% 0.18 145 / 0.2)"
                          : "oklch(78% 0.18 85 / 0.2)"
                          }`,
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                          background: d.is_registered
                            ? "var(--color-safe)"
                            : "var(--color-warn)",
                        }}
                      />
                      {d.is_registered ? "Registered" : "Unregistered"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Monitoring Panels */}
      <div className="grid lg:grid-cols-2 gap-4">
        <section className="card">
          <div className="flex items-center justify-between mb-4">
            <h2
              className="font-display font-semibold text-base"
              style={{ color: "var(--color-ink)" }}
            >
              Water Level History
            </h2>
            <span
              className="text-xs font-outlier"
              style={{
                color: "var(--color-neutral)",
              }}
            >
              Sensor #01
            </span>
          </div>
          <WaterChart />
        </section>

        <section className="card flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h2
              className="font-display font-semibold text-base flex items-center gap-2"
              style={{ color: "var(--color-ink)" }}
            >
              <Camera size={16} style={{ color: "var(--color-info)" }} />
              <span>Camera Stream · Gate A</span>
            </h2>
            <span
              className="text-xs font-outlier font-medium px-2 py-0.5 rounded"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-neutral)",
              }}
            >
              1080p · 30 FPS
            </span>
          </div>

          <div
            className="h-64 rounded-lg flex flex-col items-center justify-center p-6 text-center"
            style={{
              background: "var(--color-paper-3)",
            }}
          >
            <Camera size={32} className="mb-2" style={{ color: "var(--color-muted)" }} />
            <p
              className="text-sm font-medium"
              style={{ color: "var(--color-neutral)" }}
            >
              Live Camera Feed Standby
            </p>
            <p
              className="text-xs mt-1"
              style={{ color: "var(--color-muted)" }}
            >
              RTSP stream active · Awaiting trigger
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}