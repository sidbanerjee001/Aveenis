"use client";

import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { createClient } from "@supabase/supabase-js";

interface ChartParams {
  ticker?: string;
}

type DataPoint = {
  ticker: string;
  dataToday: number[];
  dataHistory: number[];
  score: number;
};

type GraphDataPoint = {
  name: string;
  Popularity: number;
};

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const Chart: React.FC<ChartParams> = ({ ticker = "INVALID" }) => {
  const [dataPoint, setDataPoint] = useState<DataPoint>();
  const [graphData, setGraphData] = useState<GraphDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch data from Supabase
  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data: supabaseData, error } = await supabase
          .from("final_db")
          .select("stock_ticker, data")
          .eq("stock_ticker", ticker);

        if (error) throw error;

        if (supabaseData.length === 0) {
          toast.error("No data found for this ticker.");
          return;
        }

        // Format data into the shape our component needs
        const row = supabaseData[0];
        const parsedData = JSON.parse(row.data);
        const dataTodayArray = parsedData.data_today ?? [];

        setDataPoint({
          ticker: row.stock_ticker,
          dataToday: dataTodayArray,
          dataHistory: parsedData.data_history ?? [],
          score: dataTodayArray[dataTodayArray.length - 1] ?? 0,
        });
      } catch (error) {
        console.error("Error fetching data:", error);
        toast.error("Error pulling stock data.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [ticker]);

  // Convert the "dataToday" array into "graphData"
  useEffect(() => {
    if (!dataPoint?.dataToday?.length) {
      setGraphData([]);
      return;
    }

    const formattedGraphData = dataPoint.dataToday.map((item, index) => ({
      name: `-${24-index}hrs`,
      Popularity: item ?? 0,
    }));
    setGraphData(formattedGraphData);
  }, [dataPoint]);

  if (isLoading) return <div>Loading...</div>;
  if (graphData.length === 0) return <div>No data available</div>;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={graphData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" padding={{ left: 30, right: 30 }} />
        <YAxis domain={[-100, 100]} />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="Popularity"
          stroke="#82ca9d"
          name="Popularity"
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default Chart;
