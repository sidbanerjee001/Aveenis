"use client"

import React, { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { createClient } from '@supabase/supabase-js'

type DataPoint = {
  ticker: string;
  dataToday: Array<any>;
  dataHistory: Array<any>;
  score: number;
}

type GraphDataPoint = {
  name: string;
  Popularity: number;
}

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export default function Chart() {
  const [data, setData] = useState<DataPoint[]>([]);
  const [graphData, setGraphData] = useState<GraphDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const cachedData = sessionStorage.getItem("supabaseData");
        
        if (cachedData) {
          toast.info("Pulled from session storage!");
          setData(JSON.parse(cachedData));
          return;
        }

        const { data: supabaseData, error } = await supabase
          .from('final_db')
          .select('stock_ticker, data');

        if (error) throw error;

        const formattedData: DataPoint[] = supabaseData.map(row => {
          const parsedData = JSON.parse(row.data);
          const dataTodayArray = parsedData.data_today;
          return {
            ticker: row.stock_ticker,
            dataToday: dataTodayArray,
            dataHistory: parsedData.data_history,
            score: dataTodayArray[dataTodayArray.length - 1]
          };
        });

        sessionStorage.setItem("supabaseData", JSON.stringify(formattedData));
        setData(formattedData);
      } catch (error) {
        console.error("Error fetching data:", error);
        toast.error("Error pulling stock data.");
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, []);

  useEffect(() => {
    if (data.length > 0) {
      const formattedGraphData: GraphDataPoint[] = data.map((item, index) => ({
        name: `-${24 - index}hrs`,
        Popularity: item.score
      }));
      setGraphData(formattedGraphData);
    }
  }, [data]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (graphData.length === 0) {
    return <div>No data available</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={graphData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" padding={{ left: 30, right: 30 }} />
        <YAxis domain={[-100, 100]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="Popularity" stroke="#82ca9d" name="Popularity" />
      </LineChart>
    </ResponsiveContainer>
  );
}
