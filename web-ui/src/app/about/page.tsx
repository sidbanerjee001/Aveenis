'use client'

import { useState, useRef } from 'react'
import { Dialog, DialogPanel } from '@headlessui/react'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'
import { ArrowLeftIcon } from '@heroicons/react/24/solid'

const navigation = [
  { name: 'Home', href: '/' },
  { name: 'About Us', href: 'about' },
  { name: 'Contact', href: 'contact' }
]

export default async function About() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="bg-white">
      <header className="absolute inset-x-0 top-0 z-50">
        <nav aria-label="Global" className="flex items-center justify-between p-6 lg:px-8">
          <div className="flex lg:flex-1">
            <a href="#" className="-m-1.5 p-1.5">
              <span className="sr-only">Aveenis</span>
              <p>Aveenis</p>
            </a>
          </div>
          <div className="flex lg:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-gray-700"
            >
              <span className="sr-only">Open main menu</span>
              <Bars3Icon aria-hidden="true" className="h-6 w-6" />
            </button>
          </div>
          <div className="hidden lg:flex lg:gap-x-12">
            {navigation.map((item) => (
              <a key={item.name} href={item.href} className="transition ease-in-out text-sm font-semibold leading-6 text-black hover:text-green">
                {item.name}
              </a>
            ))}
          </div>
        </nav>
        <Dialog open={mobileMenuOpen} onClose={setMobileMenuOpen} className="lg:hidden">
          <div className="fixed inset-0 z-50" />
          <DialogPanel className="fixed inset-y-0 right-0 z-50 w-full overflow-y-auto bg-white px-6 py-6 sm:max-w-sm sm:ring-1 sm:ring-black/10">
            <div className="flex items-center justify-between">
              <a href="#" className="-m-1.5 p-1.5">
                <span className="sr-only">Aveenis</span>
                <p>Aveenis</p>
              </a>
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="-m-2.5 rounded-md p-2.5 text-gray-700"
              >
                <span className="sr-only">Close menu</span>
                <XMarkIcon aria-hidden="true" className="h-6 w-6" />
              </button>
            </div>
            <div className="mt-6 flow-root">
              <div className="-my-6 divide-y divide-gray-500/10">
                <div className="space-y-2 py-6">
                  {navigation.map((item) => (
                    <a
                      key={item.name}
                      href={item.href}
                      className="transition ease-in-out -mx-3 block rounded-lg px-3 py-2 text-base font-medium leading-7 text-black hover:bg-green-hover hover:text-white"
                    >
                      {item.name}
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </DialogPanel>
        </Dialog>
      </header>

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
            <a className="inline-block" href="/"><ArrowLeftIcon className="transition ease-in-out w-6 h-6 text-black hover:text-green cursor-pointer"></ArrowLeftIcon></a>
          </div>
          <div className="text-left">
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
          </div>
        </div>
      </div>
    </div>
  )
}