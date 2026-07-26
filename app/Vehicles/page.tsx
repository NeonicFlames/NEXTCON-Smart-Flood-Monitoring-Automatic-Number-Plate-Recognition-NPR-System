export default function Vehicles(){

const vehicles = [
{
plate:"ABC1234",
time:"20:30",
confidence:"98%",
status:"Verified"
},

{
plate:"XYZ8899",
time:"20:25",
confidence:"95%",
status:"Verified"
},

{
plate:"WXX7777",
time:"20:20",
confidence:"91%",
status:"Verified"
}

]


return (

<div className="p-8 text-white">


<h1 className="
text-3xl
font-bold
text-purple-400
">

🚗 Number Plate Recognition

</h1>


<p className="text-gray-400 mt-2">

Automatic vehicle detection and plate recognition

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

Camera Status

</h2>


<p className="
text-2xl
text-green-400
font-bold
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

Vehicles Detected

</h2>


<p className="
text-3xl
text-blue-400
font-bold
mt-3
">

128

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

Latest Plate

</h2>


<p className="
text-3xl
text-purple-400
font-bold
mt-3
">

ABC1234

</p>


</div>



</div>





{/* Latest Detection */}

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

Latest Detection

</h2>



<div className="
mt-5
flex
items-center
justify-center
h-48
bg-black
rounded-xl
">


<div className="text-center">


<p className="
text-4xl
font-bold
text-purple-400
">

ABC1234

</p>


<p className="text-gray-400 mt-3">

Confidence: 98%

</p>


</div>


</div>



</section>







{/* Table */}

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
mb-5
">

Detection History

</h2>




<table className="w-full">


<thead>


<tr className="border-b border-gray-700">


<th className="text-left p-3">

Plate

</th>


<th className="text-left p-3">

Time

</th>


<th className="text-left p-3">

Confidence

</th>


<th className="text-left p-3">

Status

</th>


</tr>


</thead>





<tbody>


{
vehicles.map((vehicle,index)=>(


<tr 
key={index}
className="border-b border-gray-800"
>


<td className="p-3">

{vehicle.plate}

</td>


<td className="p-3">

{vehicle.time}

</td>


<td className="
p-3
text-purple-400
">

{vehicle.confidence}

</td>


<td className="
p-3
text-green-400
">

{vehicle.status}

</td>



</tr>


))

}



</tbody>


</table>


</section>




</div>


)

}