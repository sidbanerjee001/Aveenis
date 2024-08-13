import { useEffect, useState } from 'react';
import { 
    createColumnHelper, flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, 
    SortingState, useReactTable 
} from '@tanstack/react-table'
import { ArrowRightCircleIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { reportWebVitals } from 'next/dist/build/templates/pages';

export type Data = {
    tickerName: string;
    stat1: string;
    stat2: string;
    stat3: string;
}

const columnHelper = createColumnHelper<Data>();

// Sorting Functions are inverted for brevity... may need to write out functions!

const columns = [
    columnHelper.accessor('tickerName', {
        header: () => 'Ticker Name',
        cell: (info) => info.getValue(),
        sortingFn: 'text',
    }),
    columnHelper.accessor('stat1', {
        header: () => 'Stat 1',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    }),
    columnHelper.accessor('stat2', {
        header: () => 'Stat 2',
        cell: (info) => info.getValue(),
        sortingFn: (rowA, rowB, columnId) => {
            return parseFloat(rowB.getValue(columnId)) - parseFloat(rowA.getValue(columnId));
        },
    }),columnHelper.accessor('stat3', {
        header: () => 'Stat 3',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    })
]

export default function DataTable() {

    const [data, setData] = useState([
        {tickerName: 'av1', stat1: '4,569', stat2: '-3.42', stat3: '90.53%'},
        {tickerName: 'av2', stat1: '2,167', stat2: '+1.24', stat3: '14.29%'},
        {tickerName: 'av3', stat1: '8,513', stat2: '+2.34', stat3: '13.53%'},
        {tickerName: 'av4', stat1: '5,564', stat2: '+5.23', stat3: '21.31%'},
        {tickerName: 'av5', stat1: '4,262', stat2: '-5.34', stat3: '67.53%'},
        {tickerName: 'av6', stat1: '2,540', stat2: '+8.79', stat3: '42.61%'},
        {tickerName: 'av7', stat1: '1,265', stat2: '-9.65', stat3: '21.72%'},
    ]);
    const [columnFilters, setColumnFilters] = useState('');
    const [searchString, setSearchString] = useState('');
    const [sorting, setSorting] = useState<SortingState>([]);

    const table = useReactTable({
        data: data,
        columns,
        debugTable: true,
        getCoreRowModel: getCoreRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        getSortedRowModel: getSortedRowModel(),
        state: {
            globalFilter: columnFilters,
            sorting: sorting,
        },
        onSortingChange: setSorting,
        onGlobalFilterChange: setColumnFilters,
    })

    const handleSearch = () => {
        if (searchString.trim() !== '') {
            setColumnFilters(searchString);
        }
    };

    useEffect(() => {
        if (searchString.trim() == '') {
            setColumnFilters('');
        }
    }, [searchString]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
          handleSearch();
        }
    };

    return (
        <div className="w-3/4 mx-auto">
        <div className="relative flex flex-col min-w-0 break-words bg-white w-full mb-6 shadow-lg rounded">
          <div className="rounded-t mb-0 px-4 py-3 border-0">
            <div className="px-2 flex flex-row items-center">
                <h3 className="font-semibold text-base text-black">Popularity Metrics</h3>
                <input
                    id="price"
                    name="price"
                    type="text"
                    placeholder="Search..."
                    className="block w-100 rounded-md ml-5 border-0 py-1.5 pl-2 pr-10 text-black ring-1 ring-inset ring-gray-dark placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-green-hover sm:text-sm sm:leading-6"
                    onKeyDown={handleKeyDown}
                    value={searchString}
                    onChange={e => setSearchString(e.target.value)}
                />
                <button onClick={handleSearch}><ArrowRightCircleIcon className="transition ease-in-out ml-2 w-7 h-7 text-[#c5cbd1] hover:text-green-hover hover:cursor-pointer"/></button>
              </div>
          </div>

          <div className="block w-full overflow-x-auto">
            <table className="items-center bg-transparent w-full border-collapse table-fixed">
              <thead>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <tr key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                            <th key={header.id} className="table-header">
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
                                <div className={"flex flex-row items-center gap-x-1 " + ((cell.id as string).includes("stat2") ? ((cell.getValue() as string).includes("-") ? "text-red" : "text-green-hover") : "")}>
                                    {flexRender(
                                        cell.column.columnDef.cell,
                                        cell.getContext())
                                    }
                                    {(cell.id as string).includes("stat2") ? (
                                        <>
                                            <ChevronDownIcon className={"w-[14px] h-[14px] font-bold stroke-2 text-red " + ((cell.getValue() as string).includes("-") ? "" : "hidden")}/>
                                            <ChevronUpIcon className={"w-[12px] h-[12px] font-bold stroke-2 text-green-hover " + ((cell.getValue() as string).includes("-") ? "hidden" : "")}/>
                                        </>
                                    ) : (<></>)}
                                </div>
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