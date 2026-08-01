"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard,
  Car,
  Search,
  Waves,
  Bell,
  Settings,
  Shield,
  FolderKey,
  Lock,
  LogOut,
  UserCheck
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { isAdmin, logout, setShowLoginModal } = useAuth();

  const userNavItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "ANPR Detections", href: "/Vehicles", icon: Car },
    { name: "My Vehicle Permit", href: "/MyVehicle", icon: Search },
    { name: "Flood Monitoring", href: "/Flood", icon: Waves },
    { name: "Alerts", href: "/Alerts", icon: Bell },
  ];

  const adminNavItems = [
    { name: "Vehicle Registry", href: "/Registration", icon: FolderKey, badge: "Admin" },
    { name: "System Settings", href: "/Settings", icon: Settings },
  ];

  return (
    <aside
      className="w-64 min-h-screen flex flex-col justify-between shrink-0 select-none"
      style={{
        background: "var(--color-paper-2)",
        borderRight: "1px solid var(--color-rule)",
      }}
    >
      <div className="p-5">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3 mb-6 px-2">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 shadow-sm"
            style={{
              background: "var(--color-accent-subtle)",
              color: "var(--color-accent)",
              border: "1px solid var(--color-rule)",
            }}
          >
            <Shield size={20} />
          </div>
          <div>
            <h1
              className="font-display font-bold text-base tracking-tight leading-tight"
              style={{
                color: "var(--color-ink)",
              }}
            >
              Smart Flood NPR
            </h1>
            <p
              className="text-category mt-0.5"
              style={{
                color: "var(--color-neutral)",
              }}
            >
              SMART FLOOD DETECTION
            </p>
          </div>
        </div>

        {/* User Navigation Section */}
        <div className="mb-6">
          <p className="px-3 mb-2 text-category">
            User Portal
          </p>
          <nav className="space-y-1">
            {userNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="group flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors"
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
                >
                  <div className="flex items-center gap-2.5">
                    <Icon size={17} strokeWidth={isActive ? 2 : 1.5} />
                    <span>{item.name}</span>
                  </div>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Admin Navigation Section */}
        <div>
          <div className="flex items-center justify-between px-3 mb-2">
            <p className="text-category">
              Administration
            </p>
            {isAdmin ? (
              <span
                className="text-[11px] font-semibold px-1.5 py-0.5 rounded text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-1 font-outlier"
              >
                <UserCheck size={10} /> Active
              </span>
            ) : (
              <span className="text-[11px] font-semibold text-amber-600 flex items-center gap-1 font-outlier">
                <Lock size={10} /> Protected
              </span>
            )}
          </div>

          <nav className="space-y-1">
            {adminNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="group flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors"
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
                >
                  <div className="flex items-center gap-2.5">
                    <Icon size={17} strokeWidth={isActive ? 2 : 1.5} />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span
                      className="text-category px-1.5 py-0.5 rounded"
                      style={{
                        background: "var(--color-paper-3)",
                        color: "var(--color-accent)",
                        border: "1px solid var(--color-rule)",
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer Meta & Admin Status */}
      <div
        className="p-4 text-xs font-outlier"
        style={{
          color: "var(--color-muted)",
          borderTop: "1px solid var(--color-rule)",
        }}
      >
        {isAdmin ? (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold text-emerald-600">Admin Unlocked</span>
            </div>
            <button
              onClick={logout}
              title="Lock Admin Access"
              className="p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 text-xs transition cursor-pointer"
              style={{ color: "var(--color-danger)" }}
            >
              <LogOut size={14} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowLoginModal(true)}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 rounded-md text-xs font-semibold border transition cursor-pointer"
            style={{
              background: "var(--color-paper-3)",
              color: "var(--color-ink)",
              borderColor: "var(--color-rule)",
            }}
          >
            <Lock size={12} /> Unlock Admin Mode
          </button>
        )}

        <div className="mt-3 pt-3 border-t" style={{ borderColor: "var(--color-rule)" }}>
          <p className="font-medium text-xs font-outlier" style={{ color: "var(--color-neutral)" }}>
            NextCon System v1.0
          </p>
          <p className="mt-0.5 text-[11px] font-outlier" style={{ color: "var(--color-muted)" }}>
            Universiti Malaysia Kelantan
          </p>
        </div>
      </div>
    </aside>
  );
}
