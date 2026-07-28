import WaterChart from "@/components/WaterChart";
import { LayoutDashboard, Camera, ShieldCheck } from "lucide-react";

export default function Home() {
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
              className="text-xl font-semibold tracking-tight"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-display)",
                letterSpacing: "-0.02em",
              }}
            >
              Smart Flood & Vehicle Telemetry
            </h1>
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Real-time environmental monitoring & automatic plate recognition
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
          <ShieldCheck size={14} style={{ color: "var(--color-safe)" }} />
          <span>Telemetry Live · Gate A</span>
        </div>
      </div>

      {/* Primary Metrics */}
      <section className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card col-span-2 lg:col-span-1">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            System Status
          </p>
          <p
            className="text-lg font-semibold mt-1.5 flex items-center gap-2"
            style={{ color: "var(--color-safe)" }}
          >
            <span className="status-dot status-dot--safe" />
            Online
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Flood Condition
          </p>
          <p
            className="text-2xl font-bold mt-1"
            style={{ color: "var(--color-safe)" }}
          >
            SAFE
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Water Depth
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
            Detections Today
          </p>
          <p
            className="text-2xl font-bold mt-1"
            style={{
              color: "var(--color-ink)",
              fontFamily: "var(--font-outlier)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            128
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Latest Detection
          </p>
          <p
            className="text-2xl font-bold mt-1"
            style={{
              color: "var(--color-accent)",
              fontFamily: "var(--font-outlier)",
              letterSpacing: "0.04em",
            }}
          >
            ABC1234
          </p>
        </div>
      </section>

      {/* Vehicle Recognition Activity Table */}
      <section className="card-flush">
        <div className="px-5 pt-5 pb-3 flex items-center justify-between">
          <h2
            className="text-sm font-semibold"
            style={{ color: "var(--color-ink)" }}
          >
            Recent Vehicle Detections
          </h2>
          <span
            className="text-xs"
            style={{
              color: "var(--color-muted)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            Updated 1m ago
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
              <tr style={{ borderBottom: "1px solid var(--color-rule)" }}>
                <td
                  className="px-5 py-3 font-semibold"
                  style={{
                    color: "var(--color-accent)",
                    fontFamily: "var(--font-outlier)",
                    letterSpacing: "0.03em",
                  }}
                >
                  ABC1234
                </td>
                <td
                  className="px-5 py-3"
                  style={{
                    color: "var(--color-ink-2)",
                    fontFamily: "var(--font-outlier)",
                  }}
                >
                  8:30 PM
                </td>
                <td
                  className="px-5 py-3 font-medium"
                  style={{
                    color: "var(--color-safe)",
                    fontFamily: "var(--font-outlier)",
                  }}
                >
                  98%
                </td>
                <td className="px-5 py-3">
                  <span
                    className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full"
                    style={{
                      background: "var(--color-safe-subtle)",
                      color: "var(--color-safe)",
                      border: "1px solid oklch(70% 0.18 145 / 0.2)",
                    }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--color-safe)" }} />
                    Verified
                  </span>
                </td>
              </tr>
              <tr>
                <td
                  className="px-5 py-3 font-semibold"
                  style={{
                    color: "var(--color-accent)",
                    fontFamily: "var(--font-outlier)",
                    letterSpacing: "0.03em",
                  }}
                >
                  XYZ8899
                </td>
                <td
                  className="px-5 py-3"
                  style={{
                    color: "var(--color-ink-2)",
                    fontFamily: "var(--font-outlier)",
                  }}
                >
                  8:25 PM
                </td>
                <td
                  className="px-5 py-3 font-medium"
                  style={{
                    color: "var(--color-safe)",
                    fontFamily: "var(--font-outlier)",
                  }}
                >
                  96%
                </td>
                <td className="px-5 py-3">
                  <span
                    className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full"
                    style={{
                      background: "var(--color-safe-subtle)",
                      color: "var(--color-safe)",
                      border: "1px solid oklch(70% 0.18 145 / 0.2)",
                    }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--color-safe)" }} />
                    Verified
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Monitoring Panels */}
      <div className="grid lg:grid-cols-2 gap-4">
        <section className="card">
          <div className="flex items-center justify-between mb-4">
            <h2
              className="text-sm font-semibold"
              style={{ color: "var(--color-ink)" }}
            >
              Water Level History
            </h2>
            <span
              className="text-xs"
              style={{
                color: "var(--color-neutral)",
                fontFamily: "var(--font-outlier)",
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
              className="text-sm font-semibold flex items-center gap-2"
              style={{ color: "var(--color-ink)" }}
            >
              <Camera size={16} style={{ color: "var(--color-info)" }} />
              <span>Camera Stream · Gate A</span>
            </h2>
            <span
              className="text-xs font-medium px-2 py-0.5 rounded"
              style={{
                background: "var(--color-paper-3)",
                color: "var(--color-neutral)",
                fontFamily: "var(--font-outlier)",
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