"use client";

import { useEffect, useState } from "react";
import { Car, Camera, CheckCircle2 } from "lucide-react";
import { getRecentDetections, getTodayCount, subscribeToDetections } from "@/lib/queries/vehicles";

interface Detection {
  id: string;
  plate_number: string;
  confidence: number;
  is_registered: boolean;
  created_at: string;
}

export default function Vehicles() {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [todayCount, setTodayCount] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const [d, c] = await Promise.all([
          getRecentDetections(10),
          getTodayCount(),
        ]);
        setDetections(d as Detection[]);
        setTodayCount(c);
      } catch (e) {
        console.error("Failed to load vehicle data:", e);
      }
    }
    load();

    const sub = subscribeToDetections((newDetection) => {
      setDetections((prev) => [newDetection as Detection, ...prev.slice(0, 9)]);
      setTodayCount((c) => c + 1);
    });
    return () => { sub.unsubscribe(); };
  }, []);

  const latest = detections[0];

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
            <Car size={22} />
          </div>
          <div>
            <h1
              className="font-display font-bold text-xl tracking-tight"
              style={{
                color: "var(--color-ink)",
              }}
            >
              Automatic Number Plate Recognition (ANPR)
            </h1>
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Automated vehicle license plate extraction and verification
            </p>
          </div>
        </div>

      </div>


      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-category">
            ANPR Engine
          </p>
          <p
            className="text-lg font-display font-semibold mt-1 flex items-center gap-2"
            style={{ color: "var(--color-safe)" }}
          >
            <span className="status-dot status-dot--safe" />
            Online (YOLOv8)
          </p>
        </div>

        <div className="card">
          <p className="text-category">
            Total Detections Today
          </p>
          <p
            className="text-2xl font-outlier font-bold mt-1"
            style={{
              color: "var(--color-info)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {todayCount}
          </p>
        </div>

        <div className="card">
          <p className="text-category">
            Latest Plate Identified
          </p>
          <p
            className="text-2xl plate-number mt-1"
            style={{
              color: "var(--color-accent)",
            }}
          >
            {latest?.plate_number ?? "—"}
          </p>
        </div>
      </div>

      {/* Latest Plate Spotlight */}
      {latest && (
        <section className="card flex flex-col md:flex-row items-center justify-between gap-6 p-6">
          <div>
            <span
              className="text-category px-2.5 py-1 rounded"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-neutral)",
              }}
            >
              LATEST EXTRACTION
            </span>
            <h2
              className="text-4xl plate-number mt-3"
              style={{
                color: "var(--color-accent)",
              }}
            >
              {latest.plate_number}
            </h2>
            <p className="text-sm mt-1" style={{ color: "var(--color-neutral)" }}>
              Captured at{" "}
              {new Date(latest.created_at).toLocaleTimeString([], {
                hour: "numeric",
                minute: "2-digit",
              })}{" "}
              · Main Gate Camera
            </p>
          </div>

          <div
            className="flex items-center gap-4 px-6 py-4 rounded-lg self-stretch md:self-auto justify-center"
            style={{
              background: "var(--color-paper-3)",
            }}
          >
            <CheckCircle2 size={32} style={{ color: latest.is_registered ? "var(--color-safe)" : "var(--color-warn)" }} />
            <div>
              <p className="text-category" style={{ color: "var(--color-neutral)" }}>
                Match Confidence
              </p>
              <p
                className="text-xl font-outlier font-bold"
                style={{
                  color: latest.is_registered ? "var(--color-safe)" : "var(--color-warn)",
                }}
              >
                {(latest.confidence * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Detection History Table */}
      <section className="card-flush">
        <div className="px-5 pt-5 pb-3 flex items-center justify-between">
          <h2
            className="font-display font-semibold text-base"
            style={{ color: "var(--color-ink)" }}
          >
            Detection History Log
          </h2>
          <span
            className="text-xs font-outlier"
            style={{
              color: "var(--color-muted)",
            }}
          >
            Showing last {detections.length} entries
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--color-rule)" }}>
                <th
                  className="text-left px-5 py-2.5 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Plate Number
                </th>
                <th
                  className="text-left px-5 py-2.5 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Time
                </th>
                <th
                  className="text-left px-5 py-2.5 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Confidence
                </th>
                <th
                  className="text-left px-5 py-2.5 text-xs font-medium"
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
              {detections.map((d, index) => (
                <tr
                  key={d.id ?? index}
                  style={{
                    borderBottom:
                      index < detections.length - 1
                        ? "1px solid var(--color-rule)"
                        : "none",
                  }}
                >
                  <td
                    className="px-5 py-3 font-semibold"
                    style={{
                      color: "var(--color-accent)",
                      fontFamily: "var(--font-outlier)",
                      letterSpacing: "0.03em",
                    }}
                  >
                    {d.plate_number}
                  </td>
                  <td
                    className="px-5 py-3"
                    style={{
                      color: "var(--color-ink-2)",
                      fontFamily: "var(--font-outlier)",
                    }}
                  >
                    {new Date(d.created_at).toLocaleTimeString([], {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </td>
                  <td
                    className="px-5 py-3 font-medium"
                    style={{
                      color: "var(--color-safe)",
                      fontFamily: "var(--font-outlier)",
                    }}
                  >
                    {Math.round(d.confidence * 100)}%
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full"
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
    </div>
  );
}