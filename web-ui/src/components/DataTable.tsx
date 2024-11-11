import { useEffect, useState } from 'react';
import { 
    createColumnHelper, flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, 
    SortingState, useReactTable 
} from '@tanstack/react-table'
import { ArrowRightCircleIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

export type DataPoint = {
    ticker: string;
    stock_price: string;
    iv: string;
    pop_change: string;
    accel: string;
    pop_change_three: string;
    accel_three: string;
    raw_mentions: string;
}

const columnHelper = createColumnHelper<DataPoint>();

// Sorting Functions are inverted for brevity... may need to write out functions!

const columns = [
    columnHelper.accessor('ticker', {
        header: () => 'Ticker Name',
        cell: (info) => info.getValue(),
        sortingFn: 'text',
    }),
    columnHelper.accessor('stock_price', {
        header: () => 'Stock Price',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    }),
    columnHelper.accessor('iv', {
        header: () => 'IV',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        // sortingFn: (rowA, rowB, columnId) => {
        //     return parseFloat(rowB.getValue(columnId)) - parseFloat(rowA.getValue(columnId));
        // },
    }),columnHelper.accessor('pop_change', {
        header: () => 'Popularity Change (1D)',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    }),columnHelper.accessor('accel', {
        header: () => 'Acceleration (1D)',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    }),columnHelper.accessor('pop_change_three', {
        header: () => 'Popularity Change (3D)',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    }),columnHelper.accessor('accel_three', {
        header: () => 'Acceleration (3D)',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    }),columnHelper.accessor('raw_mentions', {
        header: () => 'Raw Score (Mentions)',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    })
]

export default function DataTable() {

    // {tickerName: 'av1', stat1: '4,569', stat2: '-3.42', stat3: '90.53%'},
    // {tickerName: 'av2', stat1: '2,167', stat2: '+1.24', stat3: '14.29%'},
    // {tickerName: 'av3', stat1: '8,513', stat2: '+2.34', stat3: '13.53%'},
    // {tickerName: 'av4', stat1: '5,564', stat2: '+5.23', stat3: '21.31%'},
    // {tickerName: 'av5', stat1: '4,262', stat2: '-5.34', stat3: '67.53%'},
    // {tickerName: 'av6', stat1: '2,540', stat2: '+8.79', stat3: '42.61%'},
    // {tickerName: 'av7', stat1: '1,265', stat2: '-9.65', stat3: '21.72%'},
    

    const [data, setData] = useState<DataPoint[]>([]);
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

    useEffect(() => {
        async function getData() {
            const { data, error } = await supabase
                .from('FrontendData')
                .select('ticker, stock_price, iv, pop_change, accel, pop_change_three, accel_three, raw_mentions');
    
            if(error) {
                console.log(error.message)
                // TODO: Implement toast notification
                return [];
            }
    
            let data_formatted = data.map((item: any) => ({
                ticker: item["ticker"].toString(),
                stock_price: item['stock_price'].toString(),
                iv: item["iv"].toString(),
                pop_change: item["pop_change"].toString(),
                accel: item["accel"].toString(), 
                pop_change_three: item["pop_change_three"].toString(), 
                accel_three: item["accel_three"].toString(), 
                raw_mentions: item["raw_mentions"].toString(), 
            }));

            setData(data_formatted);
        }

        getData();
    }, []);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
          handleSearch();
        }
    };

    function getDataValueColor(id: string, val: string) {
        if (id.includes("Ticker") || id.includes("Date")){
            return "";
        }

        if (val.includes("-")) {
            return "text-red";
        } else if (val.includes("+")) {
            return "text-green-hover"
        } else if (val.includes("%")) {
            try {
                const percentage = parseFloat(val.replace(/[^0-9a-z]/gi, ''));
                if (percentage <= 50) {
                    return "text-yellow"
                } else {
                    return "text-green-hover"
                }
            } catch (e) {
                console.log(e);
            }
        } else {
            return "";
        }
    }

    // broken
    function chevron(id: string, val: string, columns: [string]) {
        columns.forEach(element => {
            if (id.includes(element as string)) {
                if (val.includes("-")) {
                    return <ChevronDownIcon className={"w-[14px] h-[14px] font-bold stroke-2 text-red"}/>                
                } else {
                    console.log(val)
                    return <ChevronUpIcon className={"w-[12px] h-[12px] font-bold stroke-2 text-green-hover"}/>
                }
            }
        });
        return <></>
    }

    return (
        <div className="w-11/12 mx-auto">
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
                                        : "") + " inline-block my-1 text-pretty text-left",
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
                            <th key={cell.id} className={"table-entry text-left " + (cell.id.includes("ticker") ? "font-bold" : "")}>
                                <div className={"flex flex-row items-center gap-x-1 " + getDataValueColor(cell.id as string, cell.getValue() as string)}>
                                    {((cell.id as string).includes("stock_price") ? "$" : "")}
                                    {flexRender(
                                        cell.column.columnDef.cell,
                                        cell.getContext())
                                    }
                                    {chevron(cell.id as string, cell.getValue() as string, ["pop_change"])}
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