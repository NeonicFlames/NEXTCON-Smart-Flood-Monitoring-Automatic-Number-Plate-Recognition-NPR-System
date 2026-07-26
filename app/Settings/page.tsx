import {
  Settings as SettingsIcon,
  Waves,
  Cpu,
  Camera,
  Server,
  Bell,
} from "lucide-react";

export default function Settings() {
  return (
    <div className="p-8 text-white">
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-8 h-8 text-gray-200" />
        <h1 className="text-3xl font-bold text-gray-200">System Settings</h1>
      </div>

      <p className="text-gray-400 mt-2">Configure monitoring system parameters</p>

      {/* Flood Settings */}
      <section className="mt-8 bg-[#111827] border border-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Waves className="w-5 h-5 text-blue-400" />
          <span>Flood Detection Settings</span>
        </h2>

        <div className="grid grid-cols-2 gap-6 mt-5">
          <div>
            <label className="text-gray-400">Warning Level</label>
            <div className="mt-2 bg-black border border-gray-700 rounded-lg p-4">
              25 cm
            </div>
          </div>

          <div>
            <label className="text-gray-400">Danger Level</label>
            <div className="mt-2 bg-black border border-gray-700 rounded-lg p-4">
              40 cm
            </div>
          </div>
        </div>
      </section>

      {/* Hardware */}
      <section className="mt-8 bg-[#111827] border border-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-400" />
          <span>Hardware Status</span>
        </h2>

        <div className="grid grid-cols-3 gap-5 mt-5">
          <div className="bg-black rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-200 font-medium">
              <Camera className="w-4 h-4 text-blue-400" />
              <span>Camera</span>
            </div>
            <p className="text-green-400 mt-3 font-bold flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Online</span>
            </p>
          </div>

          <div className="bg-black rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-200 font-medium">
              <Waves className="w-4 h-4 text-blue-400" />
              <span>Flood Sensor</span>
            </div>
            <p className="text-green-400 mt-3 font-bold flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Connected</span>
            </p>
          </div>

          <div className="bg-black rounded-xl p-5">
            <div className="flex items-center gap-2 text-gray-200 font-medium">
              <Server className="w-4 h-4 text-blue-400" />
              <span>Server</span>
            </div>
            <p className="text-green-400 mt-3 font-bold flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Running</span>
            </p>
          </div>
        </div>
      </section>

      {/* Notification */}
      <section className="mt-8 bg-[#111827] border border-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Bell className="w-5 h-5 text-blue-400" />
          <span>Notification Settings</span>
        </h2>

        <div className="mt-5 space-y-4">
          <div className="flex justify-between bg-black p-4 rounded-lg">
            <p>Flood Alert</p>
            <p className="text-green-400">ON</p>
          </div>

          <div className="flex justify-between bg-black p-4 rounded-lg">
            <p>Emergency Notification</p>
            <p className="text-green-400">ON</p>
          </div>
        </div>
      </section>

      {/* Information */}
      <section className="mt-8 bg-[#111827] border border-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-bold">System Information</h2>

        <p className="mt-4 text-gray-400">Version: 1.0</p>
        <p className="text-gray-400">Last Update: 21 July 2026</p>
      </section>
    </div>
  );
}