"use client";

import { useSyncExternalStore } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
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
      <div className="h-64 bg-[#111827] rounded-xl flex items-center justify-center text-gray-500">
        Loading chart data...
      </div>
    );
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="time" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              borderColor: "#374151",
              color: "#fff",
              borderRadius: "0.5rem"
            }}
          />
          <Line
            type="monotone"
            dataKey="level"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={{ r: 4, fill: "#3b82f6" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
