import {
  Settings as SettingsIcon,
  Waves,
  Cpu,
  Camera,
  Server,
  Bell,
  Sliders
} from "lucide-react";

export default function Settings() {
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
              System Configuration & Hardware
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
            <div
              className="mt-1.5 rounded-md px-4 py-2.5 text-sm font-medium"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-ink)",
                fontFamily: "var(--font-outlier)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              25 cm
            </div>
          </div>

          <div>
            <label
              className="text-xs font-medium"
              style={{ color: "var(--color-neutral)" }}
            >
              Danger Evacuation Level (cm)
            </label>
            <div
              className="mt-1.5 rounded-md px-4 py-2.5 text-sm font-medium"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-ink)",
                fontFamily: "var(--font-outlier)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              40 cm
            </div>
          </div>
        </div>
      </section>

      {/* Hardware Telemetry Status — NO card-in-card nesting */}
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
          {[
            { icon: Camera, label: "ANPR Camera #01", status: "Online" },
            { icon: Waves, label: "Ultrasonic Sensor", status: "Connected" },
            { icon: Server, label: "NextCon Edge Server", status: "Running" },
          ].map(({ icon: Icon, label, status }) => (
            <div
              key={label}
              className="rounded-lg p-4"
              style={{
                background: "var(--color-paper-3)",
              }}
            >
              <div
                className="flex items-center gap-2 text-sm font-medium"
                style={{ color: "var(--color-ink)" }}
              >
                <Icon size={16} style={{ color: "var(--color-info)" }} />
                {label}
              </div>
              <p
                className="text-sm font-semibold mt-2 flex items-center gap-2"
                style={{ color: "var(--color-safe)" }}
              >
                <span className="status-dot status-dot--safe" />
                {status}
              </p>
            </div>
          ))}
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
            Broadcast & Notification Channels
          </h2>
        </div>

        <div className="space-y-2">
          {[
            { label: "SMS Broadcast on Warning Threshold", active: true },
            { label: "Emergency Evacuation Push Alert", active: true },
          ].map(({ label, active }) => (
            <div
              key={label}
              className="flex justify-between items-center rounded-md px-4 py-3"
              style={{
                background: "var(--color-paper-3)",
              }}
            >
              <p
                className="text-sm"
                style={{ color: "var(--color-ink)" }}
              >
                {label}
              </p>
              <span
                className="text-xs font-semibold px-2.5 py-1 rounded-full"
                style={{
                  background: active
                    ? "var(--color-safe-subtle)"
                    : "var(--color-paper-3)",
                  color: active
                    ? "var(--color-safe)"
                    : "var(--color-muted)",
                  border: active
                    ? "1px solid oklch(70% 0.18 145 / 0.2)"
                    : "none",
                }}
              >
                {active ? "ON" : "OFF"}
              </span>
            </div>
          ))}
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
            <p className="text-xs" style={{ color: "var(--color-muted)" }}>Last Calibration</p>
            <p className="font-medium mt-0.5" style={{ color: "var(--color-ink)", fontFamily: "var(--font-outlier)" }}>21 July 2026</p>
          </div>
          <div>
            <p className="text-xs" style={{ color: "var(--color-muted)" }}>Institution</p>
            <p className="font-medium mt-0.5" style={{ color: "var(--color-ink)" }}>UMK Bachok</p>
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