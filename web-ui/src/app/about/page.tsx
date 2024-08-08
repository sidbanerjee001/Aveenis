'use client'

import { useState, useRef } from 'react'
import { ArrowLeftIcon } from '@heroicons/react/24/solid'
import { motion } from "framer-motion"

import NavBar from '@/components/NavBar'

const navigation = [
  { name: 'Home', href: '/' },
  { name: 'About Us', href: 'about' },
  { name: 'Contact', href: 'contact' }
]

export default async function About() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="bg-white">
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
        <div className="ml-[40px] max-w-2xl py-28 sm:py-28 lg:py-28">
          <div className="mb-28">
              <motion.div
                initial={{ x: 75, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{
                  duration: 1.5,
                  ease: [0, 0.71, 0.2, 1.01]
                }}
              >
                <a className="inline-block" href="/"><ArrowLeftIcon className="transition ease-in-out w-6 h-6 text-black hover:text-green cursor-pointer"></ArrowLeftIcon></a>
              </motion.div>
            </div>
          <div className="text-left">
            <motion.div
              initial={{ x: 75, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{
                duration: 1.2,
                delay: 0.25,
                ease: [0, 0.71, 0.2, 1.01]
              }}
            >
              <h1 className="text-4xl font-bold tracking-tight text-black sm:text-6xl">
                About <span className="text-green">Us</span>
              </h1>
              <p className="mt-6 text-lg leading-8 text-gray-600">
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis dictum, sapien sit amet pharetra pulvinar, 
              ipsum elit pretium lacus, id tincidunt sem urna ac ipsum. Quisque urna orci, sollicitudin in nisl nec, 
              commodo vehicula magna. 
              <br/>
              <br/>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis dictum, sapien sit amet pharetra pulvinar, 
              ipsum elit pretium lacus, id tincidunt sem urna ac ipsum. Quisque urna orci, sollicitudin in nisl nec, 
              commodo vehicula magna. 
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}