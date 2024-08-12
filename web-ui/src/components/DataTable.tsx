import { useEffect, useState } from 'react';
import { 
    createColumnHelper, flexRender, getCoreRowModel, getSortedRowModel, SortingState, useReactTable 
} from '@tanstack/react-table'

export type Data = {
    tickerName: string;
    stat1: string;
    stat2: string;
    stat3: string;
}

const columnHelper = createColumnHelper<Data>();

const columns = [
    columnHelper.accessor('tickerName', {
        header: () => 'Ticker Name',
        cell: (info) => info.getValue(),
    }),
    columnHelper.accessor('stat1', {
        header: () => 'Stat 1',
        cell: (info) => info.getValue(),
    }),
    columnHelper.accessor('stat2', {
        header: () => 'Stat 2',
        cell: (info) => info.getValue(),
    }),columnHelper.accessor('stat3', {
        header: () => 'Stat 3',
        cell: (info) => info.getValue(),
    })
]

export default function DataTable() {

    const [data, setData] = useState([
        {tickerName: 'av1', stat1: '4,569', stat2: '340', stat3: '90.53%'},
        {tickerName: 'av2', stat1: '2,167', stat2: '124', stat3: '14.29%'},
        {tickerName: 'av3', stat1: '8,513', stat2: '234', stat3: '13.53%'},
        {tickerName: 'av4', stat1: '5,564', stat2: '523', stat3: '21.31%'},
        {tickerName: 'av5', stat1: '4,262', stat2: '534', stat3: '67.53%'},
        {tickerName: 'av6', stat1: '2,540', stat2: '879', stat3: '42.61%'},
        {tickerName: 'av7', stat1: '1,265', stat2: '965', stat3: '21.72%'},
    ]);
    const [sorting, setSorting] = useState<SortingState>([]);

    const table = useReactTable({
        data: data,
        columns,
        debugTable: true,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        state: {
            sorting
        },
        onSortingChange: setSorting
    })

    useEffect(() => {
        const order = sorting[0]?.desc ? "desc" : "asc";
        const sort = sorting[0]?.id ?? "id";
    }, [sorting])

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
            <table className="items-center bg-transparent w-full border-collapse table-fixed">
              <thead>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <tr key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                            <th className="table-header">
                                <div
                                    {...{
                                    className: (header.column.getCanSort()
                                        ? "cursor-pointer select-none"
                                        : "") + " inline-block",
                                    onClick: header.column.getToggleSortingHandler(),
                                    }}
                                >
                                {flexRender(
                                    header.column.columnDef.header,
                                    header.getContext()
                                )}
                                {
                                    (header.column.getIsSorted() as string) === "asc" ? " ↓ " : (header.column.getIsSorted() as string) === "desc" ? " ↑ " : ""
                                }
                                </div>
                            </th>
                        ))}
                    </tr>
                  ))}
              </thead>

              <tbody>

                {table.getRowModel().rows.map((row) => (
                    <tr key={row.id}>
                        {row.getVisibleCells().map((cell) => (
                            <th key={cell.id} className={"table-entry text-left " + (cell.id.includes("tickerName") ? "font-bold" : "")}>
                                {flexRender(
                                    cell.column.columnDef.cell,
                                    cell.getContext())
                                }
                            </th>
                        ))}
                    </tr>
                ))}
              </tbody>

            </table>
          </div>
        </div>
      </div>
    )
}