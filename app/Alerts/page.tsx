import { AlertCircle, AlertTriangle, ShieldAlert } from "lucide-react";

export default function Alerts() {
  const history = [
    {
      date: "21 July 2026",
      level: "42 cm",
      status: "Danger",
    },
    {
      date: "20 July 2026",
      level: "28 cm",
      status: "Warning",
    },
    {
      date: "18 July 2026",
      level: "10 cm",
      status: "Normal",
    },
  ];

  const statusStyle = (status: string) => {
    switch (status) {
      case "Danger":
        return {
          bg: "var(--color-danger-subtle)",
          color: "var(--color-danger)",
          border: "oklch(65% 0.22 25 / 0.3)",
          dot: "status-dot--danger",
        };
      case "Warning":
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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div
            className="p-2.5 rounded-lg shrink-0"
            style={{
              background: "var(--color-danger-subtle)",
              color: "var(--color-danger)",
              border: "1px solid oklch(65% 0.22 25 / 0.3)",
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
            <p className="mt-0.5 text-sm" style={{ color: "var(--color-neutral)" }}>
              Automated vehicle evacuation broadcasts and risk notifications
            </p>
          </div>
        </div>

        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs self-start sm:self-auto"
          style={{
            background: "var(--color-danger-subtle)",
            color: "var(--color-danger)",
            border: "1px solid oklch(65% 0.22 25 / 0.3)",
            fontFamily: "var(--font-outlier)",
          }}
        >
          <ShieldAlert size={14} />
          <span>Active Alert Level · Danger</span>
        </div>
      </div>

      {/* Current Danger Alert Panel — NO card-in-card nesting */}
      <section
        className="card p-6"
        style={{
          background: "var(--color-danger-subtle)",
          borderLeft: "4px solid var(--color-danger)",
          borderColor: "oklch(65% 0.22 25 / 0.3)",
        }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="status-dot status-dot--danger" />
            <span
              className="text-xs font-bold uppercase tracking-wider"
              style={{ color: "var(--color-danger)" }}
            >
              CRITICAL FLOOD ALERT
            </span>
          </div>

          <span
            className="text-xs font-medium px-2.5 py-0.5 rounded"
            style={{
              background: "var(--color-paper-2)",
              color: "var(--color-danger)",
              fontFamily: "var(--font-outlier)",
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
              color: "var(--color-danger)",
              fontFamily: "var(--font-outlier)",
            }}
          >
            42 cm
          </strong>
          , exceeding the 40 cm danger ceiling.
        </p>
      </section>

      {/* Required Evacuation Action Panel — NO card-in-card nesting */}
      <section
        className="card p-5"
        style={{
          background: "var(--color-warn-subtle)",
          borderLeft: "4px solid var(--color-warn)",
          borderColor: "oklch(78% 0.18 85 / 0.3)",
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle size={18} style={{ color: "var(--color-warn)" }} />
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--color-warn)" }}
          >
            Immediate Action Required
          </h3>
        </div>

        <p className="text-sm" style={{ color: "var(--color-ink)" }}>
          All vehicle owners parked in Zone A are instructed to relocate their vehicles immediately to higher ground at Main Building Lot C.
        </p>
      </section>

      {/* Alert History Table */}
      <section className="card-flush">
        <div className="px-5 pt-5 pb-3 flex items-center justify-between">
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
                  className="text-left px-5 py-2.5 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Date
                </th>
                <th
                  className="text-left px-5 py-2.5 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Peak Water Level
                </th>
                <th
                  className="text-left px-5 py-2.5 text-xs font-medium"
                  style={{ color: "var(--color-neutral)" }}
                >
                  Alert Status
                </th>
              </tr>
            </thead>

            <tbody>
              {history.map((item, index) => {
                const s = statusStyle(item.status);
                return (
                  <tr
                    key={index}
                    style={{
                      borderBottom:
                        index < history.length - 1
                          ? "1px solid var(--color-rule)"
                          : "none",
                    }}
                  >
                    <td
                      className="px-5 py-3"
                      style={{
                        color: "var(--color-ink)",
                        fontFamily: "var(--font-outlier)",
                      }}
                    >
                      {item.date}
                    </td>
                    <td
                      className="px-5 py-3 font-semibold"
                      style={{
                        color: "var(--color-ink)",
                        fontFamily: "var(--font-outlier)",
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {item.level}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-0.5 rounded-full"
                        style={{
                          background: s.bg,
                          color: s.color,
                          border: `1px solid ${s.border}`,
                        }}
                      >
                        <span className={`status-dot ${s.dot}`} />
                        {item.status}
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