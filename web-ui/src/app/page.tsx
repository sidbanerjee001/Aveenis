'use client'

import { useState, useRef } from 'react'
import { Dialog, DialogPanel } from '@headlessui/react'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'

const navigation = [
  { name: 'About Us', href: 'about' },
  { name: 'Contact', href: 'contact' }
]

const tableEntries = [
  {tickerName: 'av1', stat1: '4,569', stat2: '340', stat3: '90.53%'},
  {tickerName: 'av2', stat1: '2,167', stat2: '124', stat3: '14.29%'},
  {tickerName: 'av3', stat1: '8,513', stat2: '234', stat3: '13.53%'},
  {tickerName: 'av4', stat1: '5,564', stat2: '523', stat3: '21.31%'},
  {tickerName: 'av5', stat1: '4,262', stat2: '534', stat3: '67.53%'},
  {tickerName: 'av6', stat1: '2,540', stat2: '879', stat3: '42.61%'},
  {tickerName: 'av7', stat1: '1,265', stat2: '965', stat3: '21.72%'},
]

export default async function Home() {
  const tableRef = useRef<HTMLDivElement | null>(null);
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
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-black sm:text-6xl">
              Exploring the Excellence of <span className="text-green">Aveenis</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis dictum, sapien sit amet pharetra pulvinar, 
            ipsum elit pretium lacus, id tincidunt sem urna ac ipsum. Quisque urna orci, sollicitudin in nisl nec, 
            commodo vehicula magna. 
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <button onClick={() => tableRef.current?.scrollIntoView()} className="cursor-pointer transition ease-in-out select-none pt-[10px] pb-[10px] pl-[20px] pr-[20px] text-white text-sm rounded 
              shadow-black bg-green translate-y-0 hover:bg-green-hover hover:translate-y-[-2px] hover:shadow-2xl">
              Get Started
              </button>
              <a href="#" className="transition ease-in-out text-sm font-semibold leading-6 text-black hover:text-green-hover">
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
      <div ref={tableRef} className="w-3/4 mx-auto">
        <div className="relative flex flex-col min-w-0 break-words bg-white w-full mb-6 shadow-lg rounded">
          <div className="rounded-t mb-0 px-4 py-3 border-0">
            <div className="flex flex-wrap items-center">
              <div className="relative w-full px-2 max-w-full flex-grow flex-1">
                <h3 className="font-semibold text-base text-black">Popularity Metrics</h3>
              </div>
              <div className="relative w-full px-4 max-w-full flex-grow flex-1 text-right">
                <button className="bg-indigo-500 text-white active:bg-indigo-600 text-xs font-bold uppercase px-3 py-1 rounded outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150" type="button">See all</button>
              </div>
            </div>
          </div>

          <div className="block w-full overflow-x-auto">
            <table className="items-center bg-transparent w-full border-collapse ">
              <thead>
                <tr>
                  <th className="table-header">
                    Ticker
                  </th>
                  <th className="table-header">
                    Stat1
                  </th>
                  <th className="table-header">
                    Stat2
                  </th>
                  <th className="table-header">
                    Stat3
                  </th>
                </tr>
              </thead>

              <tbody>
                {tableEntries.map((tableItem, index) => (
                <tr key={index}>
                  <th className="table-entry text-left text-black">
                    {tableItem.tickerName}
                  </th>
                  <td className="table-entry">
                    {tableItem.stat1}
                  </td>
                  <td className="table-entry">
                    {tableItem.stat2}
                  </td>
                  <td className="table-entry">
                    {tableItem.stat3}
                  </td>
                </tr>
                ))}
              </tbody>

            </table>
          </div>
        </div>
      </div>
    </div>
  )
}