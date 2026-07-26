export default function Flood(){

return (

<div className="p-8 text-white">


<h1 className="
text-3xl
font-bold
text-blue-400
">

🌊 Flood Monitoring

</h1>


<p className="text-gray-400 mt-2">

Real-time water level monitoring system

</p>



{/* Top Cards */}

<div className="
grid
grid-cols-3
gap-6
mt-8
">



<div className="
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="text-gray-400">

Sensor Status

</h2>


<p className="
text-3xl
font-bold
text-green-400
mt-3
">

🟢 Online

</p>


</div>





<div className="
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="text-gray-400">

Water Level

</h2>


<p className="
text-3xl
font-bold
text-blue-400
mt-3
">

12 cm

</p>


</div>





<div className="
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="text-gray-400">

Flood Status

</h2>


<p className="
text-3xl
font-bold
text-green-400
mt-3
">

SAFE

</p>


</div>



</div>





{/* Flood Status */}

<section className="
mt-8
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="text-xl font-bold">

Current Condition

</h2>



<div className="
mt-5
bg-green-900/30
border
border-green-500
rounded-xl
p-6
">


<p className="
text-3xl
font-bold
text-green-400
">

🟢 SAFE

</p>


<p className="text-gray-300 mt-2">

Water level is currently normal.

</p>


</div>



</section>






{/* Water Level Visualization */}

<section className="
mt-8
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="text-xl font-bold">

Water Level History

</h2>



<div className="
mt-5
h-40
bg-blue-950
rounded-xl
flex
items-center
justify-center
border
border-blue-500
">


<p className="
text-blue-300
">

Chart will display sensor readings

</p>


</div>


</section>






{/* Threshold */}

<section className="
mt-8
bg-[#111827]
border
border-gray-800
rounded-xl
p-6
">


<h2 className="text-xl font-bold">

Flood Threshold Settings

</h2>



<div className="
grid
grid-cols-2
gap-5
mt-5
">



<div className="
bg-yellow-900/30
border
border-yellow-500
rounded-xl
p-5
">


<p className="text-yellow-300">

⚠ Warning Level

</p>


<p className="text-3xl font-bold mt-2">

25 cm

</p>


</div>




<div className="
bg-red-900/30
border
border-red-500
rounded-xl
p-5
">


<p className="text-red-300">

🚨 Danger Level

</p>


<p className="text-3xl font-bold mt-2">

40 cm

</p>


</div>



</div>


</section>




</div>

)

}