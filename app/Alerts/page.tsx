import { AlertTriangle, AlertCircle } from "lucide-react";

export default function Alerts() {
  const history = [
    {
      date: "21 July 2026",
      level: "42 cm",
      status: "Danger",
    },
    {
      date: "20 July 2026",
      level: "28 cm",
      status: "Warning",
    },
    {
      date: "18 July 2026",
      level: "10 cm",
      status: "Normal",
    },
  ];

  return (
    <div className="p-8 text-white">
      <div className="flex items-center gap-3">
        <AlertCircle className="w-8 h-8 text-red-400" />
        <h1 className="text-3xl font-bold text-red-400">Flood Alerts</h1>
      </div>

      <p className="text-gray-400 mt-2">
        Emergency notification and flood warning management
      </p>

      {/* Current Alert */}
      <section className="mt-8 bg-[#111827] border border-red-500 rounded-xl p-6">
        <h2 className="text-xl font-bold">Current Alert Status</h2>

        <div className="mt-5 bg-red-900/30 border border-red-500 rounded-xl p-6">
          <p className="text-4xl font-bold text-red-400 flex items-center gap-3">
            <span className="w-4 h-4 rounded-full bg-red-500 animate-ping inline-block" />
            <span>DANGER</span>
          </p>

          <p className="text-xl mt-3">
            Flood detected in Student Parking Zone A
          </p>

          <p className="text-gray-300 mt-3">Water Level: 42 cm</p>
        </div>
      </section>

      {/* Action Message */}
      <section className="mt-8 bg-[#111827] border border-yellow-500 rounded-xl p-6">
        <h2 className="text-xl font-bold text-yellow-400 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          <span>Required Action</span>
        </h2>

        <p className="text-lg mt-4">
          Please remove your vehicle immediately to avoid flood damage.
        </p>
      </section>

      {/* Alert History */}
      <section className="mt-8 bg-[#111827] border border-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-bold mb-5">Alert History</h2>

        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left p-3">Date</th>
              <th className="text-left p-3">Water Level</th>
              <th className="text-left p-3">Status</th>
            </tr>
          </thead>

          <tbody>
            {history.map((item, index) => (
              <tr key={index} className="border-b border-gray-800">
                <td className="p-3">{item.date}</td>
                <td className="p-3">{item.level}</td>
                <td
                  className={
                    item.status === "Danger"
                      ? "text-red-400 p-3 font-bold"
                      : item.status === "Warning"
                      ? "text-yellow-400 p-3 font-bold"
                      : "text-green-400 p-3 font-bold"
                  }
                >
                  {item.status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}