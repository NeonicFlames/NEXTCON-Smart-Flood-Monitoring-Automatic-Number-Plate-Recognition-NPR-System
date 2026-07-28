import { Waves, AlertTriangle, ShieldAlert, Activity } from "lucide-react";

export default function Flood() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div
            className="p-2.5 rounded-lg shrink-0"
            style={{
              background: "var(--color-paper-2)",
              color: "var(--color-info)",
              border: "1px solid var(--color-rule)",
            }}
          >
            <Waves size={22} />
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
              Flood Water Level Monitoring
            </h1>
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Ultrasonic telemetry and automated water rise detection
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
          <Activity size={14} style={{ color: "var(--color-safe)" }} />
          <span>Telemetry Polling · 5s</span>
        </div>
      </div>

      {/* Primary Telemetry Metrics */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Sensor Health
          </p>
          <p
            className="text-lg font-semibold mt-1.5 flex items-center gap-2"
            style={{ color: "var(--color-safe)" }}
          >
            <span className="status-dot status-dot--safe" />
            Active & Calibrated
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Current Water Depth
          </p>
          <p
            className="text-2xl font-bold mt-1"
            style={{
              color: "var(--color-info)",
              fontFamily: "var(--font-outlier)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            12 cm
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Overall Risk State
          </p>
          <p
            className="text-2xl font-bold mt-1"
            style={{ color: "var(--color-safe)" }}
          >
            SAFE
          </p>
        </div>
      </section>

      {/* Current Environmental State — NO card-in-card nesting */}
      <section
        className="card"
        style={{
          background: "var(--color-safe-subtle)",
          border: "1px solid oklch(70% 0.18 145 / 0.3)",
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="w-3 h-3 rounded-full" style={{ background: "var(--color-safe)" }} />
            <h2
              className="text-lg font-bold"
              style={{ color: "var(--color-safe)" }}
            >
              Normal Water Conditions
            </h2>
          </div>
          <span
            className="text-xs font-medium px-2.5 py-0.5 rounded-full"
            style={{
              background: "var(--color-paper-2)",
              color: "var(--color-safe)",
              border: "1px solid oklch(70% 0.18 145 / 0.3)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            LEVEL OK
          </span>
        </div>

        <p className="text-sm mt-3" style={{ color: "var(--color-ink-2)" }}>
          Water level is currently 12 cm, well below the 25 cm alert threshold. No action required for campus parking areas.
        </p>
      </section>

      {/* Flood Alert Threshold Parameters — NO card-in-card nesting */}
      <section className="card">
        <h2
          className="text-sm font-semibold mb-4"
          style={{ color: "var(--color-ink)" }}
        >
          Configured Alert Thresholds
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            className="p-4 rounded-lg"
            style={{
              background: "var(--color-warn-subtle)",
              borderLeft: "3px solid var(--color-warn)",
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
              25 cm
            </p>
            <p className="text-xs mt-1" style={{ color: "var(--color-neutral)" }}>
              Triggers warning notifications to security personnel
            </p>
          </div>

          <div
            className="p-4 rounded-lg"
            style={{
              background: "var(--color-danger-subtle)",
              borderLeft: "3px solid var(--color-danger)",
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
              40 cm
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