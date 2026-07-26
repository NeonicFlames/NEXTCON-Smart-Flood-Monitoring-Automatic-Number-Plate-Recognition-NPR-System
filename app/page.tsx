import WaterChart from "@/components/WaterChart";
import { Camera } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0B1220] p-8 text-white">
      {/* Header */}
      <h1 className="text-3xl font-bold text-blue-500">
        Smart Flood Monitoring & NPR System
      </h1>

      <p className="text-gray-400 mt-2">
        Real-time flood detection and vehicle monitoring dashboard
      </p>

      {/* Status Cards */}
      <section className="grid lg:grid-cols-5 gap-5 mt-8">
        <div className="bg-[#111827] p-6 rounded-xl shadow border border-gray-800">
          <h2 className="text-gray-400">System Status</h2>
          <p className="text-2xl font-bold text-green-400 mt-3 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" /> Online
          </p>
        </div>

        <div className="bg-[#111827] p-6 rounded-xl shadow border border-gray-800">
          <h2 className="text-gray-400">Flood Status</h2>
          <p className="text-3xl font-bold text-green-400 mt-3">SAFE</p>
        </div>

        <div className="bg-[#111827] p-6 rounded-xl shadow border border-gray-800">
          <h2 className="text-gray-400">Water Level</h2>
          <p className="text-3xl font-bold text-blue-400 mt-3">12 cm</p>
        </div>

        <div className="bg-[#111827] p-6 rounded-xl shadow border border-gray-800">
          <h2 className="text-gray-400">Vehicles Today</h2>
          <p className="text-3xl font-bold mt-3">128</p>
        </div>

        <div className="bg-[#111827] p-6 rounded-xl shadow border border-gray-800">
          <h2 className="text-gray-400">Latest Plate</h2>
          <p className="text-3xl font-bold text-purple-400 mt-3">ABC1234</p>
        </div>
      </section>

      {/* Vehicle Table */}
      <section className="bg-[#111827] mt-8 p-6 rounded-xl shadow border border-gray-800">
        <h2 className="text-xl font-bold mb-5">Recent Vehicle Detection</h2>

        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400">
              <th className="text-left p-3">Plate Number</th>
              <th className="text-left p-3">Time</th>
              <th className="text-left p-3">Confidence</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-800/50">
              <td className="p-3 font-semibold text-purple-300">ABC1234</td>
              <td className="p-3 text-gray-300">8:30 PM</td>
              <td className="p-3 text-green-400 font-medium">98%</td>
            </tr>
            <tr>
              <td className="p-3 font-semibold text-purple-300">XYZ8899</td>
              <td className="p-3 text-gray-300">8:25 PM</td>
              <td className="p-3 text-green-400 font-medium">96%</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* Flood & Camera Monitoring Grid */}
      <div className="grid lg:grid-cols-2 gap-8 mt-8">
        <section className="bg-[#111827] p-6 rounded-xl shadow border border-gray-800">
          <h2 className="text-xl font-bold mb-5">Water Level Monitoring</h2>
          <WaterChart />
        </section>

        <section className="bg-[#111827] p-6 rounded-xl shadow border border-gray-800">
          <h2 className="text-xl font-bold mb-5 flex items-center gap-2">
            <Camera className="w-5 h-5 text-blue-400" />
            <span>Camera Monitoring</span>
          </h2>
          <div className="h-64 bg-black rounded-xl flex items-center justify-center border border-gray-800">
            <p className="text-gray-500 font-medium">Live Camera Feed Waiting...</p>
          </div>
        </section>
      </div>
    </div>
  );
}