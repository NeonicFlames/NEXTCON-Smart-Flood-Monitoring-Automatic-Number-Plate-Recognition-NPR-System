"use client";

import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface PageHeaderProps {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  /** Optional right-aligned actions (buttons, badges, status pills) */
  actions?: ReactNode;
  /** Override the icon chip accent (e.g. danger for Alerts) */
  accent?: "default" | "danger" | "safe" | "warn";
}

const accentStyles: Record<NonNullable<PageHeaderProps["accent"]>, {
  bg: string;
  color: string;
  border: string;
}> = {
  default: {
    bg: "var(--color-accent-subtle)",
    color: "var(--color-accent)",
    border: "#2b4a75",
  },
  danger: {
    bg: "var(--color-danger-subtle)",
    color: "var(--color-danger)",
    border: "#5c2226",
  },
  safe: {
    bg: "var(--color-safe-subtle)",
    color: "var(--color-safe)",
    border: "#1d4a3a",
  },
  warn: {
    bg: "var(--color-warn-subtle)",
    color: "var(--color-warn)",
    border: "#4d3a1a",
  },
};

export default function PageHeader({
  icon: Icon,
  title,
  subtitle,
  actions,
  accent = "default",
}: PageHeaderProps) {
  const a = accentStyles[accent];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-start gap-4">
        <div
          className="icon-chip shrink-0"
          style={{
            background: a.bg,
            color: a.color,
            border: `1px solid ${a.border}`,
          }}
        >
          <Icon size={22} />
        </div>
        <div>
          <h1
            className="font-display font-bold text-xl tracking-tight"
            style={{ color: "var(--color-ink)" }}
          >
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1 text-sm" style={{ color: "var(--color-neutral)" }}>
              {subtitle}
            </p>
          )}
        </div>
      </div>

      {actions && (
        <div className="flex items-center gap-2 self-start sm:self-auto">
          {actions}
        </div>
      )}
    </div>
  );
}
