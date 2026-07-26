export default function Settings(){

return (

<div className="p-8 text-white">


<h1 className="
text-3xl
font-bold
text-gray-200
">

⚙ System Settings

</h1>


<p className="text-gray-400 mt-2">

Configure monitoring system parameters

</p>





{/* Flood Settings */}

<section className="
mt-8
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="
text-xl
font-bold
">

🌊 Flood Detection Settings

</h2>



<div className="
grid
grid-cols-2
gap-6
mt-5
">



<div>


<label className="text-gray-400">

Warning Level

</label>


<div className="
mt-2
bg-black
border
border-gray-700
rounded-lg
p-4
">

25 cm

</div>


</div>





<div>


<label className="text-gray-400">

Danger Level

</label>


<div className="
mt-2
bg-black
border
border-gray-700
rounded-lg
p-4
">

40 cm

</div>


</div>



</div>


</section>






{/* Hardware */}

<section className="
mt-8
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="
text-xl
font-bold
">

🔌 Hardware Status

</h2>



<div className="
grid
grid-cols-3
gap-5
mt-5
">



<div className="
bg-black
rounded-xl
p-5
">

📷 Camera

<p className="
text-green-400
mt-3
font-bold
">

🟢 Online

</p>

</div>





<div className="
bg-black
rounded-xl
p-5
">

🌊 Flood Sensor

<p className="
text-green-400
mt-3
font-bold
">

🟢 Connected

</p>

</div>





<div className="
bg-black
rounded-xl
p-5
">

🖥 Server

<p className="
text-green-400
mt-3
font-bold
">

🟢 Running

</p>

</div>



</div>


</section>






{/* Notification */}

<section className="
mt-8
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="
text-xl
font-bold
">

🔔 Notification Settings

</h2>



<div className="
mt-5
space-y-4
">



<div className="
flex
justify-between
bg-black
p-4
rounded-lg
">


<p>
Flood Alert
</p>


<p className="
text-green-400
">

ON

</p>


</div>





<div className="
flex
justify-between
bg-black
p-4
rounded-lg
">


<p>
Emergency Notification
</p>


<p className="
text-green-400
">

ON

</p>


</div>



</div>


</section>







{/* Information */}

<section className="
mt-8
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="
text-xl
font-bold
">

System Information

</h2>



<p className="
mt-4
text-gray-400
">

Version: 1.0

</p>


<p className="
text-gray-400
">

Last Update: 21 July 2026

</p>


</section>




</div>

)

}