"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";
import { getReadingHistory, subscribeToFloodReadings } from "@/lib/queries/flood";

const emptySubscribe = () => () => { };

function useIsClient() {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
}

interface ChartPoint {
  time: string;
  level: number;
}

export default function WaterChart() {
  const isClient = useIsClient();
  const [data, setData] = useState<ChartPoint[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const readings = await getReadingHistory(20);
        setData(
          readings.map((r: { created_at: string; depth_cm: number }) => ({
            time: new Date(r.created_at).toLocaleTimeString([], {
              hour: "numeric",
              minute: "2-digit",
            }),
            level: Number(Number(r.depth_cm).toFixed(2)),
          }))
        );
      } catch (e) {
        console.error("Failed to load chart data:", e);
      }
    }
    load();

    const sub = subscribeToFloodReadings((newReading) => {
      const r = newReading as { created_at: string; depth_cm: number };
      setData((prev) => [
        ...prev.slice(-19),
        {
          time: new Date(r.created_at).toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
          }),
          level: Number(Number(r.depth_cm).toFixed(2)),
        },
      ]);
    });

    return () => {
      sub.unsubscribe();
    };
  }, []);

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

  if (data.length === 0) {
    return (
      <div
        className="h-64 rounded-lg flex items-center justify-center text-sm"
        style={{
          background: "var(--color-paper-3)",
          color: "var(--color-muted)",
        }}
      >
        No flood readings yet
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="waterGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="oklch(66% 0.20 250)" stopOpacity={0.4} />
              <stop offset="60%" stopColor="oklch(72% 0.16 235)" stopOpacity={0.12} />
              <stop offset="100%" stopColor="oklch(72% 0.16 235)" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="waterStroke" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="oklch(66% 0.20 250)" />
              <stop offset="100%" stopColor="oklch(72% 0.16 235)" />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="oklch(30% 0.012 255)"
            vertical={false}
          />
          <XAxis
            dataKey="time"
            stroke="oklch(70% 0.010 255)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="oklch(70% 0.010 255)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            unit=" cm"
          />
          <Tooltip
            contentStyle={{
              background: "oklch(17% 0.014 255)",
              borderColor: "oklch(30% 0.012 255)",
              color: "oklch(96% 0.006 255)",
              borderRadius: "0.75rem",
              fontSize: "var(--text-xs)",
              fontFamily: "var(--font-outlier)",
              boxShadow: "var(--shadow-pop)",
            }}
            labelStyle={{ color: "oklch(70% 0.010 255)", fontFamily: "var(--font-outlier)" }}
          />
          <Area
            type="monotone"
            dataKey="level"
            stroke="url(#waterStroke)"
            strokeWidth={2.5}
            fill="url(#waterGradient)"
            dot={{ r: 3, fill: "oklch(66% 0.20 250)", strokeWidth: 0 }}
            activeDot={{ r: 5, fill: "oklch(66% 0.20 250)", strokeWidth: 2, stroke: "oklch(13% 0.012 255)" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
