import { useEffect, useState } from 'react';
import { 
    Cell,
    createColumnHelper, flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, 
    SortingState, useReactTable 
} from '@tanstack/react-table'
import { ArrowRightCircleIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { createClient } from '@supabase/supabase-js'
import { useRouter } from 'next/navigation'
import { Slide, ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

export type DataPoint = {
    ticker: string;
    dataToday: Array<any>;
    stock_price: number;
    market_cap: number;
    score: number;
}

const columnHelper = createColumnHelper<DataPoint>();

// Sorting Functions are inverted for brevity... may need to write out functions!

const columns = [
    columnHelper.accessor('ticker', {
        header: () => 'Ticker Name',
        cell: (info) => info.getValue(),
        sortingFn: 'text',
    }),
    columnHelper.accessor('score', {
        header: () => 'Popularity Score',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    }),
    columnHelper.accessor('stock_price', {
        header: () => 'Stock Price',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        // sortingFn: (rowA, rowB, columnId) => {
        //     return parseFloat(rowB.getValue(columnId)) - parseFloat(rowA.getValue(columnId));
        // },
    }),columnHelper.accessor('market_cap', {
        header: () => 'Market Cap',
        cell: (info) => info.getValue(),
        sortingFn: 'alphanumeric',
        invertSorting: true
    })
    // ,columnHelper.accessor('accel', {
    //     header: () => 'Acceleration (1D)',
    //     cell: (info) => info.getValue(),
    //     sortingFn: 'alphanumeric',
    //     invertSorting: true
    // }),columnHelper.accessor('pop_change_three', {
    //     header: () => 'Popularity Change (3D)',
    //     cell: (info) => info.getValue(),
    //     sortingFn: 'alphanumeric',
    //     invertSorting: true
    // }),columnHelper.accessor('accel_three', {
    //     header: () => 'Acceleration (3D)',
    //     cell: (info) => info.getValue(),
    //     sortingFn: 'alphanumeric',
    //     invertSorting: true
    // }),columnHelper.accessor('raw_mentions', {
    //     header: () => 'Raw Score (Mentions)',
    //     cell: (info) => info.getValue(),
    //     sortingFn: 'alphanumeric',
    //     invertSorting: true
    // })
]

export default function DataTable() {

    const [data, setData] = useState<DataPoint[]>([]);
    const [columnFilters, setColumnFilters] = useState('');
    const [searchString, setSearchString] = useState('');
    const [sorting, setSorting] = useState<SortingState>([]);
    const router = useRouter();

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
            // const cachedData = sessionStorage.getItem("supabaseData");
            
            // if (cachedData) {
            //     toast.info("Pulled from session storage!");
            //     console.log(JSON.parse(cachedData));
            //     setData(JSON.parse(cachedData));
            //     return;
            // }
            const { data, error } = await supabase
                .from('full_data_with_accel')
                .select('ticker, stock_price, market_cap, daily_score');
    
            if(error) {
                console.log(error.message)
                toast.error("Error pulling stock data.");
                return [];
            }
    
            const dataFormatted: DataPoint[] = data.map(row => {
                const daily_score = JSON.parse(row.daily_score);
                const market_cap_formatted = JSON.parse(row.market_cap).map((num: number) => +(num / 1e9).toFixed(2));
                return {
                    ticker: row.ticker,
                    dataToday: daily_score,
                    score: daily_score,
                    stock_price: Number(JSON.parse(row.stock_price).at(-1).toFixed(2)),
                    market_cap: market_cap_formatted.at(-1)
                    // Additional table data appended here
                }
            });
            
            sessionStorage.setItem("supabaseData", JSON.stringify(dataFormatted));
            setData(dataFormatted);
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

    function generateTableRender(cell: Cell<DataPoint, unknown>) {

        if (cell.id.includes("ticker")) {
            const tickerName = cell.getValue() as string;
            return (
                <th key={cell.id} className={"table-entry text-center font-semibold"}>
                    <div className={"flex flex-row items-center gap-x-1"}>
                    <a href={"graph/" + tickerName} className={"inline transition ease-in-out bg-green-select text-green-select-text w-14 rounded-md py-1 hover:text-green-hover"}>
                        {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext())
                        }
                        </a>
                    </div>
                </th>
            )
        } else {
            return (
                <th key={cell.id} className={"table-entry text-left"}>
                    <div className={"flex flex-row items-center gap-x-1"}>
                        {(((cell.id as string).includes("stock_price") || (cell.id as string).includes("market_cap"))? "$" : "")}
                        {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext())
                        }
                        {((cell.id as string).includes("market_cap") ? "B" : "")}
                    </div>
                </th>
            )
        }
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
                    <tr key={row.id} onClick={() => router.push('/graph/'+(row.getVisibleCells().at(0)?.getValue()))} className="transition ease-in-out cursor-pointer bg-white hover:bg-gray-dark">
                        {row.getVisibleCells().map((cell) => (
                            generateTableRender(cell)
                        ))}
                    </tr>
                ))}
              </tbody>

            </table>
          </div>
        </div>
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