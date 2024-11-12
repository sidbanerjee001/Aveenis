'use client'

import { useState, useRef, useEffect } from 'react'
import { Slide, ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Cookies from 'js-cookie';

import NavBar from '@/components/NavBar'
import DataTable from '@/components/DataTable'
import Footer from '@/components/footer'

export default function Home() {
  const tableRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<HTMLDivElement | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    if (!Cookies.get('visited')) {
      toast.info("Click a Ticker Name to see timeseries data.");
      Cookies.set('visited', 'true', { expires: 7 });
  }
  }, [])

  return (
    <div className="bg-white dark:bg-black transition-colors duration-300 transition ease-in-out">
      <NavBar/>

      <div className="relative isolate px-6 pt-14 lg:px-8 h-screen w-screen">
        <div
          aria-hidden="true"
          className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80"
        >
          <div
            style={{
              clipPath:
                'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
            }}
            className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-green to-[#34a0a4] opacity-30 sm:left-[calc(50%-45rem)] sm:w-[72.1875rem]"
          />
        </div>
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-black sm:text-6xl dark:text-white">
              Exploring the Excellence of <span className="text-green dark:text-green-400 glow-text dark:glow-text">Aveenis</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 dark:text-white">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis dictum, sapien sit amet pharetra pulvinar, 
            ipsum elit pretium lacus, id tincidunt sem urna ac ipsum. Quisque urna orci, sollicitudin in nisl nec, 
            commodo vehicula magna. 
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <button onClick={() => tableRef.current?.scrollIntoView()} className="cursor-pointer transition ease-in-out select-none pt-[10px] pb-[10px] pl-[20px] pr-[20px] text-white text-sm rounded 
              shadow-black bg-green translate-y-0 hover:bg-green-hover hover:translate-y-[-2px] hover:shadow-2xl dark:shadow-green-techno/80 dark:bg-green-techno">
              View Data
              </button>
              <a href="about" className="transition ease-in-out text-sm font-semibold leading-6 text-black hover:text-green-hover dark:text-white dark:hover:text-green-techno">
                Learn more <span aria-hidden="true">→</span>
              </a>
            </div>
          </div>
        </div>
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-[calc(100%-13rem)] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[calc(100%-30rem)]"
        >
          <div
            style={{
              clipPath:
                'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
            }}
            className="relative left-[calc(50%+3rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 bg-gradient-to-tr from-green to-[#34a0a4] opacity-30 sm:left-[calc(50%+36rem)] sm:w-[72.1875rem]"
          />
        </div>
      </div>

      <div ref={tableRef}><DataTable/></div>
      <Footer/>
      <ToastContainer
        position="bottom-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
        transition={Slide}
      />
    </div>
  )
}