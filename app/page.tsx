import WaterChart from "@/components/WaterChart";
export default function Home() {
  return (
    <main className="min-h-screen bg-[#0B1220] p-8 text-white">

      {/* Header */}
      <h1 className="text-3xl font-bold text-blue-700">
        Smart Flood Monitoring & NPR System
      </h1>

      <p className="text-gray-600 mt-2">
        Real-time flood detection and vehicle monitoring dashboard
      </p>


      {/* Navigation */}
      <nav className="mt-6 bg-[#111827] p-4 rounded-xl shadow border border-gray-800">
        <ul className="flex gap-8 font-medium text-gray-300">
          <li>Dashboard</li>
          <li>Vehicles</li>
          <li>Flood Monitoring</li>
          <li>Alerts</li>
          <li>Settings</li>
        </ul>
      </nav>



      {/* Status Cards */}
      <section className="
      grid 
      lg:grid-cols-5 
      gap-5 
      mt-8
      ">
        <div className="
bg-[#111827]
p-6
rounded-xl
shadow
border
border-gray-800
">

<h2 className="text-gray-400">

System Status

</h2>


<p className="
text-2xl
font-bold
text-green-400
mt-3
">

🟢 Online

</p>


</div>


        <div className="bg-[#111827] p-6 rounded-xl shadow">
          <h2 className="text-gray-400">
            Flood Status
          </h2>

          <p className="text-3xl font-bold text-green-400 mt-3">
            SAFE
          </p>
        </div>



        <div className="bg-[#111827] p-6 rounded-xl shadow">

          <h2 className="text-gray-400">
            Water Level
          </h2>

          <p className="text-3xl font-bold text-blue-400 mt-3">
            12 cm
          </p>

        </div>




        <div className="bg-[#111827] p-6 rounded-xl shadow">

          <h2 className="text-gray-400">
            Vehicles Today
          </h2>

          <p className="text-3xl font-bold mt-3">
            128
          </p>

        </div>




        <div className="bg-[#111827] p-6 rounded-xl shadow">

          <h2 className="text-gray-400">
            Latest Plate
          </h2>

          <p className="text-3xl font-bold text-purple-400 mt-3">
            ABC1234
          </p>

        </div>


      </section>



      {/* Vehicle Table */}

      <section className="bg-[#111827] mt-8 p-6 rounded-xl shadow border border-gray-800">

        <h2 className="text-xl font-bold mb-5">
          Recent Vehicle Detection
        </h2>


        <table className="w-full">

          <thead>

            <tr className="border-b">

              <th className="text-left p-3">
                Plate Number
              </th>

              <th className="text-left p-3">
                Time
              </th>

              <th className="text-left p-3">
                Confidence
              </th>

            </tr>

          </thead>


          <tbody>

            <tr className="border-b">

              <td className="p-3">
                ABC1234
              </td>

              <td className="p-3">
                8:30 PM
              </td>

              <td className="p-3">
                98%
              </td>

            </tr>


            <tr>

              <td className="p-3">
                XYZ8899
              </td>

              <td className="p-3">
                8:25 PM
              </td>

              <td className="p-3">
                96%
              </td>

            </tr>


          </tbody>


        </table>


      </section>



      {/* Flood Monitoring */}

      <section className="bg-[#111827] mt-8 p-6 rounded-xl shadow">

        <h2 className="text-xl font-bold">
          Water Level Monitoring
        </h2>


        <section className="
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
mt-8
">


<h2 className="
text-xl
font-bold
">

 Water Level Monitoring

</h2>


<div className="mt-5">

<WaterChart/>

</div>


</section>
<section className="
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
mt-8
">


<h2 className="text-xl font-bold">

📷 Camera Monitoring

</h2>


<div className="
h-52
bg-black
rounded-xl
mt-5
flex
items-center
justify-center
">


<p className="text-gray-500">

Camera Feed Waiting...

</p>


</div>


</section>


      </section>


    </main>
  );
}