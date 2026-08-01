"use client";

import { usePathname } from "next/navigation";

const routeTitles: Record<string, string> = {
  "/": "Dashboard Overview",
  "/Vehicles": "Vehicle Recognition",
  "/Flood": "Flood Monitoring",
  "/Alerts": "Emergency Alerts",
  "/Settings": "System Settings",
};

export default function Header() {
  const pathname = usePathname();
  const title = routeTitles[pathname] ?? "Dashboard Overview";

  return (
    <header
      className="h-16 flex items-center justify-between px-6 lg:px-8 shrink-0 select-none"
      style={{
        background: "var(--color-paper)",
        borderBottom: "1px solid var(--color-rule)",
      }}
    >
      <div className="flex items-center gap-3">
        <h2
          className="font-display font-semibold text-base tracking-tight"
          style={{
            color: "var(--color-ink)",
          }}
        >
          {title}
        </h2>
      </div>

      <div
        className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium font-outlier"
        style={{
          background: "var(--color-safe-subtle)",
          color: "var(--color-safe)",
          border: "1px solid oklch(70% 0.18 145 / 0.2)",
        }}
      >
        <span className="status-dot status-dot--safe" />
        <span>ONLINE</span>
      </div>
    </header>
  );
}