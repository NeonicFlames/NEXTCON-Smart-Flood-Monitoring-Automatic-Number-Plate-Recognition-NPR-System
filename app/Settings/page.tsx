"use client";

import { useEffect, useState } from "react";
import {
  Settings as SettingsIcon,
  Waves,
  Cpu,
  Camera,
  Server,
  Bell,
  Sliders
} from "lucide-react";
import { getSettings, updateSetting, getCameras } from "@/lib/queries/settings";
import { getRegisteredVehicles } from "@/lib/queries/vehicles";

interface CameraRecord {
  id: string;
  name: string;
  model: string;
  location: string;
  resolution: string;
  is_active: boolean;
}

export default function Settings() {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [cameras, setCameras] = useState<CameraRecord[]>([]);
  const [vehicleCount, setVehicleCount] = useState(0);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [s, c, v] = await Promise.all([
          getSettings(),
          getCameras(),
          getRegisteredVehicles(),
        ]);
        setSettings(s);
        setCameras(c as CameraRecord[]);
        setVehicleCount(v.length);
      } catch (e) {
        console.error("Failed to load settings:", e);
      }
    }
    load();
  }, []);

  async function handleUpdateSetting(key: string, value: string) {
    setSaving(key);
    try {
      await updateSetting(key, value);
      setSettings((prev) => ({ ...prev, [key]: value }));
    } catch (e) {
      console.error("Failed to update setting:", e);
    }
    setSaving(null);
  }

  const warningThreshold = settings.warning_threshold_cm ?? "25";
  const dangerThreshold = settings.danger_threshold_cm ?? "40";
  const telegramEnabled = settings.telegram_enabled === "true";
  const pushEnabled = settings.push_enabled === "true";

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div
            className="p-2.5 rounded-lg shrink-0"
            style={{
              background: "var(--color-paper-2)",
              color: "var(--color-neutral)",
              border: "1px solid var(--color-rule)",
            }}
          >
            <SettingsIcon size={22} />
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
              System Configuration &amp; Hardware
            </h1>
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Manage sensor thresholds, camera feeds, and alert notifications
            </p>
          </div>
        </div>

        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs self-start sm:self-auto"
          style={{
            background: "var(--color-paper-2)",
            color: "var(--color-neutral)",
            border: "1px solid var(--color-rule)",
            fontFamily: "var(--font-outlier)",
          }}
        >
          <Sliders size={14} style={{ color: "var(--color-accent)" }} />
          <span>Config Profile · UMK-Default</span>
        </div>
      </div>

      {/* Threshold Configuration */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Waves size={16} style={{ color: "var(--color-info)" }} />
          <h2
            className="text-sm font-semibold"
            style={{ color: "var(--color-ink)" }}
          >
            Flood Detection Water Thresholds
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              className="text-xs font-medium"
              style={{ color: "var(--color-neutral)" }}
            >
              Warning Trigger Level (cm)
            </label>
            <input
              type="number"
              value={warningThreshold}
              onChange={(e) => handleUpdateSetting("warning_threshold_cm", e.target.value)}
              className="mt-1.5 rounded-md px-4 py-2.5 text-sm font-medium w-full"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-ink)",
                fontFamily: "var(--font-outlier)",
                fontVariantNumeric: "tabular-nums",
                border: "1px solid var(--color-rule)",
                outline: "none",
              }}
              disabled={saving === "warning_threshold_cm"}
            />
          </div>

          <div>
            <label
              className="text-xs font-medium"
              style={{ color: "var(--color-neutral)" }}
            >
              Danger Evacuation Level (cm)
            </label>
            <input
              type="number"
              value={dangerThreshold}
              onChange={(e) => handleUpdateSetting("danger_threshold_cm", e.target.value)}
              className="mt-1.5 rounded-md px-4 py-2.5 text-sm font-medium w-full"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-ink)",
                fontFamily: "var(--font-outlier)",
                fontVariantNumeric: "tabular-nums",
                border: "1px solid var(--color-rule)",
                outline: "none",
              }}
              disabled={saving === "danger_threshold_cm"}
            />
          </div>
        </div>
      </section>

      {/* Hardware Telemetry Status */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Cpu size={16} style={{ color: "var(--color-info)" }} />
          <h2
            className="text-sm font-semibold"
            style={{ color: "var(--color-ink)" }}
          >
            Hardware Component Diagnostics
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {cameras.map((cam) => (
            <div
              key={cam.id}
              className="rounded-lg p-4"
              style={{ background: "var(--color-paper-3)" }}
            >
              <div
                className="flex items-center gap-2 text-sm font-medium"
                style={{ color: "var(--color-ink)" }}
              >
                <Camera size={16} style={{ color: "var(--color-info)" }} />
                {cam.name}
              </div>
              <p className="text-xs mt-1" style={{ color: "var(--color-neutral)" }}>
                {cam.model} · {cam.resolution}
              </p>
              <p
                className="text-sm font-semibold mt-2 flex items-center gap-2"
                style={{ color: cam.is_active ? "var(--color-safe)" : "var(--color-neutral)" }}
              >
                <span className={`status-dot ${cam.is_active ? "status-dot--safe" : "status-dot--warn"}`} />
                {cam.is_active ? "Online" : "Standby"}
              </p>
            </div>
          ))}

          <div
            className="rounded-lg p-4"
            style={{ background: "var(--color-paper-3)" }}
          >
            <div
              className="flex items-center gap-2 text-sm font-medium"
              style={{ color: "var(--color-ink)" }}
            >
              <Waves size={16} style={{ color: "var(--color-info)" }} />
              Ultrasonic Sensor
            </div>
            <p
              className="text-sm font-semibold mt-2 flex items-center gap-2"
              style={{ color: "var(--color-safe)" }}
            >
              <span className="status-dot status-dot--safe" />
              Connected
            </p>
          </div>

          <div
            className="rounded-lg p-4"
            style={{ background: "var(--color-paper-3)" }}
          >
            <div
              className="flex items-center gap-2 text-sm font-medium"
              style={{ color: "var(--color-ink)" }}
            >
              <Server size={16} style={{ color: "var(--color-info)" }} />
              NextCon Edge Server
            </div>
            <p
              className="text-sm font-semibold mt-2 flex items-center gap-2"
              style={{ color: "var(--color-safe)" }}
            >
              <span className="status-dot status-dot--safe" />
              Running
            </p>
          </div>
        </div>
      </section>

      {/* Notification Preferences */}
      <section className="card">
        <div className="flex items-center gap-2 mb-4">
          <Bell size={16} style={{ color: "var(--color-info)" }} />
          <h2
            className="text-sm font-semibold"
            style={{ color: "var(--color-ink)" }}
          >
            Broadcast &amp; Notification Channels
          </h2>
        </div>

        <div className="space-y-2">
          <div
            className="flex justify-between items-center rounded-md px-4 py-3"
            style={{ background: "var(--color-paper-3)" }}
          >
            <p className="text-sm" style={{ color: "var(--color-ink)" }}>
              Telegram Broadcast on Warning Threshold
            </p>
            <button
              onClick={() => handleUpdateSetting("telegram_enabled", telegramEnabled ? "false" : "true")}
              className="text-xs font-semibold px-2.5 py-1 rounded-full cursor-pointer"
              style={{
                background: telegramEnabled ? "var(--color-safe-subtle)" : "var(--color-paper-3)",
                color: telegramEnabled ? "var(--color-safe)" : "var(--color-muted)",
                border: telegramEnabled ? "1px solid oklch(70% 0.18 145 / 0.2)" : "1px solid var(--color-rule)",
              }}
            >
              {telegramEnabled ? "ON" : "OFF"}
            </button>
          </div>

          <div
            className="flex justify-between items-center rounded-md px-4 py-3"
            style={{ background: "var(--color-paper-3)" }}
          >
            <p className="text-sm" style={{ color: "var(--color-ink)" }}>
              Emergency Evacuation Push Alert
            </p>
            <button
              onClick={() => handleUpdateSetting("push_enabled", pushEnabled ? "false" : "true")}
              className="text-xs font-semibold px-2.5 py-1 rounded-full cursor-pointer"
              style={{
                background: pushEnabled ? "var(--color-safe-subtle)" : "var(--color-paper-3)",
                color: pushEnabled ? "var(--color-safe)" : "var(--color-muted)",
                border: pushEnabled ? "1px solid oklch(70% 0.18 145 / 0.2)" : "1px solid var(--color-rule)",
              }}
            >
              {pushEnabled ? "ON" : "OFF"}
            </button>
          </div>
        </div>
      </section>

      {/* System Information */}
      <section className="card">
        <h2
          className="text-sm font-semibold mb-3"
          style={{ color: "var(--color-ink)" }}
        >
          System Information
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-xs" style={{ color: "var(--color-muted)" }}>Framework</p>
            <p className="font-medium mt-0.5" style={{ color: "var(--color-ink)" }}>NextCon v1.0</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: "var(--color-muted)" }}>Registered Vehicles</p>
            <p className="font-medium mt-0.5" style={{ color: "var(--color-ink)", fontFamily: "var(--font-outlier)" }}>{vehicleCount}</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: "var(--color-muted)" }}>Institution</p>
            <p className="font-medium mt-0.5" style={{ color: "var(--color-ink)" }}>UMK</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: "var(--color-muted)" }}>Faculty</p>
            <p className="font-medium mt-0.5" style={{ color: "var(--color-ink)" }}>FSDK</p>
          </div>
        </div>
      </section>
    </div>
  );
}