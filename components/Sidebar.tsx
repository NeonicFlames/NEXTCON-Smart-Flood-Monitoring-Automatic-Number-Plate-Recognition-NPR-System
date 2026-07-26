"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Car,
  Waves,
  Bell,
  Settings
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
    <aside className="w-64 min-h-screen bg-[#111827] border-r border-gray-800 p-6 flex flex-col justify-between">
      <div>
        <h1 className="text-xl font-bold text-blue-400 mb-10 flex items-center gap-2">
          <span>🌊</span> Smart Flood NPR
        </h1>

        <nav className="space-y-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                  isActive
                    ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}