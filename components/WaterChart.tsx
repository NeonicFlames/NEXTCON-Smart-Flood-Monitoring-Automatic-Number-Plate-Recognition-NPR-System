"use client";

import { useSyncExternalStore } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

const emptySubscribe = () => () => { };

function useIsClient() {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
}

const data = [
  { time: "8:00", level: 10 },
  { time: "8:15", level: 12 },
  { time: "8:30", level: 18 },
  { time: "8:45", level: 25 },
  { time: "9:00", level: 32 }
];

export default function WaterChart() {
  const isClient = useIsClient();

  if (!isClient) {
    return (
      <div
        className="h-64 rounded-lg flex items-center justify-center text-sm"
        style={{
          background: "var(--color-paper-3)",
          color: "var(--color-muted)",
        }}
      >
        Loading chart data…
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="waterGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="oklch(65% 0.20 250)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="oklch(65% 0.20 250)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="oklch(28% 0.010 250)"
            vertical={false}
          />
          <XAxis
            dataKey="time"
            stroke="oklch(68% 0.008 250)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="oklch(68% 0.008 250)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            unit=" cm"
          />
          <Tooltip
            contentStyle={{
              background: "oklch(18% 0.012 250)",
              borderColor: "oklch(28% 0.010 250)",
              color: "oklch(95% 0.005 250)",
              borderRadius: "0.5rem",
              fontSize: "0.8rem",
              boxShadow: "0 4px 12px oklch(0% 0 0 / 0.4)",
            }}
            labelStyle={{ color: "oklch(68% 0.008 250)" }}
          />
          <Area
            type="monotone"
            dataKey="level"
            stroke="oklch(65% 0.20 250)"
            strokeWidth={2}
            fill="url(#waterGradient)"
            dot={{ r: 3, fill: "oklch(65% 0.20 250)", strokeWidth: 0 }}
            activeDot={{ r: 5, fill: "oklch(65% 0.20 250)", strokeWidth: 2, stroke: "oklch(14% 0.010 250)" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
