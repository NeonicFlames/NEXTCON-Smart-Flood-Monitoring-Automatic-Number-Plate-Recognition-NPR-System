"use client";

import { useEffect, useState } from "react";
import { AlertCircle, ShieldAlert, Check } from "lucide-react";
import {
  getActiveFloodAlerts,
  getAlertHistory,
  acknowledgeAlert,
  subscribeToAlerts,
} from "@/lib/queries/alerts";
import { getLatestReading } from "@/lib/queries/flood";

interface FloodAlert {
  id: string;
  plate_number: string;
  flood_level_cm: number;
  alert_type: string;
  message: string;
  is_notified: boolean;
  is_acknowledged: boolean;
  created_at: string;
  registered_vehicles?: {
    owner_name: string;
    phone: string;
    zone: string;
  } | null;
}

interface FloodReading {
  depth_cm: number;
  status: string;
}

export default function Alerts() {
  const [activeAlerts, setActiveAlerts] = useState<FloodAlert[]>([]);
  const [history, setHistory] = useState<FloodAlert[]>([]);
  const [reading, setReading] = useState<FloodReading | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [active, hist, r] = await Promise.all([
          getActiveFloodAlerts(),
          getAlertHistory(20),
          getLatestReading(),
        ]);
        setActiveAlerts(active as FloodAlert[]);
        setHistory(hist as FloodAlert[]);
        setReading(r);
      } catch (e) {
        console.error("Failed to load alerts:", e);
      }
    }
    load();

    const sub = subscribeToAlerts((newAlert) => {
      setActiveAlerts((prev) => [newAlert as FloodAlert, ...prev]);
      setHistory((prev) => [newAlert as FloodAlert, ...prev]);
    });
    return () => { sub.unsubscribe(); };
  }, []);

  async function handleAcknowledge(alertId: string) {
    try {
      await acknowledgeAlert(alertId);
      setActiveAlerts((prev) => prev.filter((a) => a.id !== alertId));
      setHistory((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_acknowledged: true } : a))
      );
    } catch (e) {
      console.error("Failed to acknowledge alert:", e);
    }
  }

  const status = reading?.status ?? "SAFE";
  const depth = reading?.depth_cm ?? 0;
  const depthDisplay = depth.toFixed(2);
  const hasActiveAlerts = activeAlerts.length > 0 || status === "DANGER" || status === "WARNING";

  const statusStyle = (alertType: string) => {
    switch (alertType) {
      case "DANGER":
        return {
          bg: "var(--color-danger-subtle)",
          color: "var(--color-danger)",
          border: "oklch(65% 0.22 25 / 0.3)",
          dot: "status-dot--danger",
        };
      case "WARNING":
        return {
          bg: "var(--color-warn-subtle)",
          color: "var(--color-warn)",
          border: "oklch(78% 0.18 85 / 0.3)",
          dot: "status-dot--warn",
        };
      default:
        return {
          bg: "var(--color-safe-subtle)",
          color: "var(--color-safe)",
          border: "oklch(70% 0.18 145 / 0.3)",
          dot: "status-dot--safe",
        };
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div
            className="icon-chip"
            style={{
              background: "var(--color-danger-subtle)",
              color: "var(--color-danger)",
              border: "1px solid oklch(66% 0.22 25 / 0.3)",
            }}
          >
            <AlertCircle size={22} />
          </div>
          <div>
            <h1
              className="text-xl font-semibold tracking-tight"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-display)",
                letterSpacing: "-0.02em",
              }}
            >
              Emergency Flood Alerts
            </h1>
            <p className="mt-1 text-sm" style={{ color: "var(--color-neutral)" }}>
              Automated vehicle evacuation broadcasts and risk notifications
            </p>
          </div>
        </div>

        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs self-start sm:self-auto"
          style={{
            background: hasActiveAlerts ? "var(--color-danger-subtle)" : "var(--color-safe-subtle)",
            color: hasActiveAlerts ? "var(--color-danger)" : "var(--color-safe)",
            border: `1px solid ${hasActiveAlerts ? "oklch(66% 0.22 25 / 0.3)" : "oklch(72% 0.18 145 / 0.3)"}`,
            fontFamily: "var(--font-outlier)",
            boxShadow: hasActiveAlerts ? "var(--shadow-glow-danger)" : "var(--shadow-glow-safe)",
          }}
        >
          <ShieldAlert size={14} />
          <span>
            {hasActiveAlerts
              ? `Active Alert Level · ${status}`
              : "No Active Alerts"}
          </span>
        </div>
      </div>

      {/* Current Alert Panel */}
      {hasActiveAlerts && (
        <section
          className="card p-6"
          style={{
            background: status === "DANGER" ? "var(--color-danger-subtle)" : "var(--color-warn-subtle)",
            borderLeft: `4px solid ${status === "DANGER" ? "var(--color-danger)" : "var(--color-warn)"}`,
            borderColor: status === "DANGER" ? "oklch(66% 0.22 25 / 0.3)" : "oklch(80% 0.18 85 / 0.3)",
            boxShadow: status === "DANGER" ? "var(--shadow-glow-danger)" : "var(--shadow-glow-warn)",
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className={`status-dot ${status === "DANGER" ? "status-dot--danger" : "status-dot--warn"}`} />
              <span
                className="text-xs font-bold uppercase tracking-wider"
                style={{ color: status === "DANGER" ? "var(--color-danger)" : "var(--color-warn)" }}
              >
                {status === "DANGER" ? "CRITICAL FLOOD ALERT" : "FLOOD WARNING"}
              </span>
            </div>

            <span
              className="text-xs font-medium px-2.5 py-0.5 rounded-full"
              style={{
                background: "var(--color-paper-2)",
                color: status === "DANGER" ? "var(--color-danger)" : "var(--color-warn)",
                fontFamily: "var(--font-outlier)",
                border: `1px solid ${status === "DANGER" ? "oklch(66% 0.22 25 / 0.3)" : "oklch(80% 0.18 85 / 0.3)"}`,
              }}
            >
              BROADCAST ACTIVE
            </span>
          </div>

          <h2
            className="text-2xl font-bold mt-3"
            style={{ color: "var(--color-ink)" }}
          >
            Flood Detected in Student Parking Zone A
          </h2>

          <p className="text-sm mt-2" style={{ color: "var(--color-ink-2)" }}>
            Water sensor reading is currently{" "}
            <strong
              style={{
                color: status === "DANGER" ? "var(--color-danger)" : "var(--color-warn)",
                fontFamily: "var(--font-outlier)",
              }}
            >
              {depthDisplay} cm
            </strong>
            , exceeding the {status === "DANGER" ? "40 cm danger" : "25 cm warning"} ceiling.
          </p>
        </section>
      )}

      {/* Active Alerts with Acknowledge */}
      {activeAlerts.length > 0 && (
        <section className="card">
          <h2
            className="text-sm font-semibold mb-4"
            style={{ color: "var(--color-ink)" }}
          >
            Unacknowledged Alerts ({activeAlerts.length})
          </h2>
          <div className="space-y-3">
            {activeAlerts.map((alert) => {
              const s = statusStyle(alert.alert_type);
              return (
                <div
                  key={alert.id}
                  className="flex items-center justify-between rounded-xl p-4"
                  style={{ background: s.bg, border: `1px solid ${s.border}` }}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`status-dot ${s.dot}`} />
                      <span
                        className="text-xs font-bold uppercase tracking-wider"
                        style={{ color: s.color }}
                      >
                        {alert.alert_type}
                      </span>
                      <span
                        className="text-sm font-bold"
                        style={{ color: "var(--color-accent)", fontFamily: "var(--font-outlier)", letterSpacing: "0.03em" }}
                      >
                        {alert.plate_number}
                      </span>
                    </div>
                    <p className="text-xs truncate" style={{ color: "var(--color-ink-2)" }}>
                      {alert.message}
                    </p>
                    {alert.registered_vehicles && (
                      <p className="text-xs mt-0.5" style={{ color: "var(--color-neutral)" }}>
                        Owner: {alert.registered_vehicles.owner_name} · {alert.registered_vehicles.phone}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    className="btn-ghost shrink-0 ml-4 inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 cursor-pointer"
                  >
                    <Check size={14} />
                    Acknowledge
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Alert History Table */}
      <section className="card-flush">
        <div className="px-6 pt-6 pb-4 flex items-center justify-between">
          <h2
            className="text-sm font-semibold"
            style={{ color: "var(--color-ink)" }}
          >
            Incident History Log
          </h2>
          <span
            className="text-xs"
            style={{
              color: "var(--color-muted)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            Archived Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid var(--color-rule)" }}>
                <th
                  className="text-left px-6 py-3 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Date
                </th>
                <th
                  className="text-left px-6 py-3 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Vehicle
                </th>
                <th
                  className="text-left px-6 py-3 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Peak Water Level
                </th>
                <th
                  className="text-left px-6 py-3 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Alert Status
                </th>
              </tr>
            </thead>

            <tbody>
              {history.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-sm" style={{ color: "var(--color-muted)" }}>
                    No alert history
                  </td>
                </tr>
              )}
              {history.map((item, index) => {
                const s = statusStyle(item.alert_type);
                return (
                  <tr
                    key={item.id ?? index}
                    style={{
                      borderBottom:
                        index < history.length - 1
                          ? "1px solid var(--color-rule)"
                          : "none",
                    }}
                  >
                    <td
                      className="px-6 py-3.5"
                      style={{
                        color: "var(--color-ink)",
                        fontFamily: "var(--font-outlier)",
                      }}
                    >
                      {new Date(item.created_at).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "long",
                        year: "numeric",
                      })}
                    </td>
                    <td
                      className="px-6 py-3.5 font-semibold"
                      style={{
                        color: "var(--color-accent)",
                        fontFamily: "var(--font-outlier)",
                        letterSpacing: "0.03em",
                      }}
                    >
                      {item.plate_number}
                    </td>
                    <td
                      className="px-6 py-3.5 font-semibold"
                      style={{
                        color: "var(--color-ink)",
                        fontFamily: "var(--font-outlier)",
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {Number(item.flood_level_cm).toFixed(2)} cm
                    </td>
                    <td className="px-6 py-3.5">
                      <span
                        className="badge"
                        style={{
                          background: s.bg,
                          color: s.color,
                          border: `1px solid ${s.border}`,
                        }}
                      >
                        <span className={`status-dot ${s.dot}`} />
                        {item.alert_type}
                        {item.is_acknowledged && " · Ack"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}