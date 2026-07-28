"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Car,
  Waves,
  Bell,
  Settings,
  Shield
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Vehicles", href: "/Vehicles", icon: Car },
    { name: "Flood Monitoring", href: "/Flood", icon: Waves },
    { name: "Alerts", href: "/Alerts", icon: Bell },
    { name: "Settings", href: "/Settings", icon: Settings }
  ];

  return (
    <aside
      className="w-60 min-h-screen flex flex-col justify-between shrink-0 select-none"
      style={{
        background: "var(--color-paper-2)",
        borderRight: "1px solid var(--color-rule)",
      }}
    >
      <div className="p-5">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3 mb-8 px-2">
          <div
            className="w-8 h-8 rounded-md flex items-center justify-center shrink-0"
            style={{
              background: "var(--color-accent-subtle)",
              color: "var(--color-accent)",
              border: "1px solid var(--color-rule)",
            }}
          >
            <Shield size={18} />
          </div>
          <div>
            <h1
              className="text-sm font-semibold tracking-tight leading-tight"
              style={{
                color: "var(--color-ink)",
                fontFamily: "var(--font-display)",
              }}
            >
              Smart Flood NPR
            </h1>
            <p
              className="text-xs"
              style={{
                color: "var(--color-neutral)",
                fontFamily: "var(--font-outlier)",
                fontSize: "0.68rem",
              }}
            >
              UMK MONITORING
            </p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className="group flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors"
                style={{
                  background: isActive
                    ? "var(--color-accent-subtle)"
                    : "transparent",
                  color: isActive
                    ? "var(--color-accent)"
                    : "var(--color-neutral)",
                  borderLeft: isActive
                    ? "2px solid var(--color-accent)"
                    : "2px solid transparent",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = "var(--color-paper-3)";
                    e.currentTarget.style.color = "var(--color-ink)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.color = "var(--color-neutral)";
                  }
                }}
              >
                <Icon size={18} strokeWidth={isActive ? 2 : 1.5} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Meta */}
      <div
        className="p-5 text-xs"
        style={{
          color: "var(--color-muted)",
          fontFamily: "var(--font-outlier)",
          borderTop: "1px solid var(--color-rule)",
        }}
      >
        <p className="font-medium" style={{ color: "var(--color-neutral)" }}>
          NextCon System v1.0
        </p>
        <p className="mt-0.5" style={{ fontSize: "0.68rem" }}>
          Faculty of Bioengineering & Technology
        </p>
      </div>
    </aside>
  );
}
