"use client";

import {
LineChart,
Line,
XAxis,
YAxis,
Tooltip,
ResponsiveContainer
} from "recharts";


const data = [

{
time:"8:00",
level:10
},

{
time:"8:15",
level:12
},

{
time:"8:30",
level:18
},

{
time:"8:45",
level:25
},

{
time:"9:00",
level:32
}

];


export default function WaterChart(){

return (

<div className="h-64">


<ResponsiveContainer width="100%" height="100%">


<LineChart data={data}>


<XAxis dataKey="time"/>


<YAxis/>



<Tooltip/>




<Line
type="monotone"
dataKey="level"
stroke="#3b82f6"
strokeWidth={3}
/>



</LineChart>


</ResponsiveContainer>


</div>


)

}