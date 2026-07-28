import { Car, Camera, CheckCircle2 } from "lucide-react";

export default function Vehicles() {
  const vehicles = [
    {
      plate: "ABC1234",
      time: "8:30 PM",
      confidence: "98%",
      status: "Verified",
    },
    {
      plate: "XYZ8899",
      time: "8:25 PM",
      confidence: "96%",
      status: "Verified",
    },
    {
      plate: "WXX7777",
      time: "8:20 PM",
      confidence: "91%",
      status: "Verified",
    },
  ];

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
              className="text-xl font-semibold tracking-tight"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-display)",
                letterSpacing: "-0.02em",
              }}
            >
              Number Plate Recognition (ANPR)
            </h1>
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Automated vehicle license plate extraction and verification
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
          <Camera size={14} style={{ color: "var(--color-accent)" }} />
          <span>Camera #01 · Active</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            ANPR Engine
          </p>
          <p
            className="text-lg font-semibold mt-1.5 flex items-center gap-2"
            style={{ color: "var(--color-safe)" }}
          >
            <span className="status-dot status-dot--safe" />
            Online (YOLOv8)
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Total Detections Today
          </p>
          <p
            className="text-2xl font-bold mt-1"
            style={{
              color: "var(--color-info)",
              fontFamily: "var(--font-outlier)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            128
          </p>
        </div>

        <div className="card">
          <p className="text-xs font-medium" style={{ color: "var(--color-neutral)" }}>
            Latest Plate Identified
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
      </div>

      {/* Latest Plate Spotlight — NO card-in-card nesting */}
      <section className="card flex flex-col md:flex-row items-center justify-between gap-6 p-6">
        <div>
          <span
            className="text-xs font-medium px-2.5 py-1 rounded"
            style={{
              background: "var(--color-paper-3)",
              color: "var(--color-neutral)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            LATEST EXTRACTION
          </span>
          <h2
            className="text-4xl font-extrabold mt-3 tracking-wider"
            style={{
              color: "var(--color-accent)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            ABC1234
          </h2>
          <p className="text-sm mt-1" style={{ color: "var(--color-neutral)" }}>
            Captured at 8:30 PM · Student Zone A Access Gate
          </p>
        </div>

        <div
          className="flex items-center gap-4 px-6 py-4 rounded-lg self-stretch md:self-auto justify-center"
          style={{
            background: "var(--color-paper-3)",
          }}
        >
          <CheckCircle2 size={32} style={{ color: "var(--color-safe)" }} />
          <div>
            <p
              className="text-xs font-medium uppercase tracking-wide"
              style={{ color: "var(--color-neutral)" }}
            >
              Match Confidence
            </p>
            <p
              className="text-xl font-bold"
              style={{
                color: "var(--color-safe)",
                fontFamily: "var(--font-outlier)",
              }}
            >
              98.4%
            </p>
          </div>
        </div>
      </section>

      {/* Detection History Table */}
      <section className="card-flush">
        <div className="px-5 pt-5 pb-3 flex items-center justify-between">
          <h2
            className="text-sm font-semibold"
            style={{ color: "var(--color-ink)" }}
          >
            Detection History Log
          </h2>
          <span
            className="text-xs"
            style={{
              color: "var(--color-muted)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            Showing last 3 entries
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
              {vehicles.map((vehicle, index) => (
                <tr
                  key={index}
                  style={{
                    borderBottom:
                      index < vehicles.length - 1
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
                    {vehicle.plate}
                  </td>
                  <td
                    className="px-5 py-3"
                    style={{
                      color: "var(--color-ink-2)",
                      fontFamily: "var(--font-outlier)",
                    }}
                  >
                    {vehicle.time}
                  </td>
                  <td
                    className="px-5 py-3 font-medium"
                    style={{
                      color: "var(--color-safe)",
                      fontFamily: "var(--font-outlier)",
                    }}
                  >
                    {vehicle.confidence}
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
                      {vehicle.status}
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