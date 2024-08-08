import { BeakerIcon } from "@heroicons/react/24/outline"

const tableEntries = [
    {tickerName: 'av1', stat1: '4,569', stat2: '340', stat3: '90.53%'},
    {tickerName: 'av2', stat1: '2,167', stat2: '124', stat3: '14.29%'},
    {tickerName: 'av3', stat1: '8,513', stat2: '234', stat3: '13.53%'},
    {tickerName: 'av4', stat1: '5,564', stat2: '523', stat3: '21.31%'},
    {tickerName: 'av5', stat1: '4,262', stat2: '534', stat3: '67.53%'},
    {tickerName: 'av6', stat1: '2,540', stat2: '879', stat3: '42.61%'},
    {tickerName: 'av7', stat1: '1,265', stat2: '965', stat3: '21.72%'},
  ]

export default async function DataTable() {
    return (
        <div className="w-3/4 mx-auto">
        <div className="relative flex flex-col min-w-0 break-words bg-white w-full mb-6 shadow-lg rounded">
          <div className="rounded-t mb-0 px-4 py-3 border-0">
            <div className="flex flex-row items-center">
              <div className="px-2">
                <h3 className="font-semibold text-base text-black">Popularity Metrics</h3>
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
    )
}