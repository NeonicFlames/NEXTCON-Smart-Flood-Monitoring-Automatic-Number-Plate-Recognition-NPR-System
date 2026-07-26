import {
  LayoutDashboard,
  Car,
  Waves,
  Bell,
  Settings
} from "lucide-react";


export default function Sidebar(){

return (

<aside className="
w-64
min-h-screen
bg-[#111827]
border-r
border-gray-800
p-6
">


<h1 className="
text-xl
font-bold
text-blue-400
mb-10
">
 Smart Flood NPR
</h1>


<nav className="space-y-5">


<div className="flex items-center gap-3 text-gray-300 hover:text-white cursor-pointer">

<LayoutDashboard size={20}/>

<a href="/">
Dashboard
</a>

</div>



<div className="flex items-center gap-3 text-gray-300 hover:text-white cursor-pointer">

<Car size={20}/>

<a href="/Vehicles">
Vehicles
</a>

</div>



<a
href="/Flood"
className="flex items-center gap-3 text-gray-300 hover:text-white cursor-pointer"
>

<Waves size={20}/>

Flood Monitoring

</a>



<a
href="/Alerts"
className="flex items-center gap-3 text-gray-300 hover:text-white cursor-pointer"
>

<Bell size={20}/>

Alerts

</a>



<a
href="/Settings"
className="flex items-center gap-3 text-gray-300 hover:text-white cursor-pointer"
>

<Settings size={20}/>

Settings

</a>


</nav>


</aside>


)

}