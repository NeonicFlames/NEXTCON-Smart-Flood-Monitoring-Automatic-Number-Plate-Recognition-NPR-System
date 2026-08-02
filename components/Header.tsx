"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Activity, ChevronRight, ShieldCheck } from "lucide-react";

const routeTitles: Record<string, string> = {
  "/": "Dashboard Overview",
  "/Vehicles": "Vehicle Recognition",
  "/Flood": "Flood Monitoring",
  "/Alerts": "Emergency Alerts",
  "/Settings": "System Settings",
  "/Registration": "Vehicle Registry",
  "/MyVehicle": "My Vehicle Permit",
};

export default function Header() {
  const pathname = usePathname();
  const title = routeTitles[pathname] ?? "Dashboard Overview";

  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- clock needs client-only initial value to avoid hydration mismatch
    setNow(new Date());
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const time = now
    ? now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : "—";
  const date = now
    ? now.toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" })
    : "";

  return (
    <header
      className="h-16 flex items-center justify-between px-6 lg:px-8 shrink-0 select-none"
      style={{
        background: "var(--color-paper-2)",
        borderBottom: "1px solid var(--color-rule)",
      }}
    >
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 min-w-0">
        <span
          className="text-xs font-outlier hidden sm:inline"
          style={{ color: "var(--color-muted)" }}
        >
          UMK
        </span>
        <ChevronRight
          size={12}
          className="hidden sm:block"
          style={{ color: "var(--color-muted)" }}
        />
        <h2
          className="font-display font-semibold text-base tracking-tight truncate"
          style={{ color: "var(--color-ink)" }}
        >
          {title}
        </h2>
      </div>

      {/* Right cluster */}
      <div className="flex items-center gap-3">
        {/* Live clock */}
        <div
          className="hidden md:flex flex-col items-end leading-tight"
          style={{ color: "var(--color-neutral)" }}
        >
          <span className="text-sm font-outlier font-semibold tabular" style={{ color: "var(--color-ink)" }}>
            {time}
          </span>
          <span className="text-[10px] font-outlier uppercase tracking-wider" style={{ color: "var(--color-muted)" }}>
            {date}
          </span>
        </div>

        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium font-outlier"
          style={{
            background: "var(--color-safe-subtle)",
            color: "var(--color-safe)",
            border: "1px solid #1d4a3a",
          }}
        >
          <span className="status-dot status-dot--safe" />
          <span>ONLINE</span>
          <Activity size={12} className="opacity-70" />
        </div>

        <div
          className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
          style={{
            background: "var(--color-accent)",
            color: "#ffffff",
          }}
        >
          <ShieldCheck size={16} />
        </div>
      </div>
    </header>
  );
}