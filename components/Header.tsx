export default function Header() {

  return (

    <header className="
h-20
bg-[#111827]
border-b
border-gray-800
flex
items-center
justify-between
px-8
">


      <h2 className="
text-xl
font-semibold
text-white
">

        Dashboard

      </h2>



      <div className="flex items-center gap-2 text-gray-400">
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
        <span>System Online</span>
      </div>


    </header>

  )

}