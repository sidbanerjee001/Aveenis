'use client'
import React, { PureComponent } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const dummy_data = [
    {
      name: '11/11',
      PopularityChange: -78.25,
      Acceleration: 23.2,
    },
    {
      name: '11/10',
      PopularityChange: -58.34,
      Acceleration: 24,
    },
    {
      name: '11/10',
      PopularityChange: -20.4,
      Acceleration: 29,
    },
    {
      name: '11/9',
      PopularityChange: -40.4,
      Acceleration: 40,
    },
    {
      name: '11/8',
      PopularityChange: -80.4,
      Acceleration: 10,
    },
    {
      name: '11/7',
      PopularityChange: -99.2,
      Acceleration: 2,
    },
    {
      name: '11/6',
      PopularityChange: -99.4,
      Acceleration: 34,
    },
  ];

export default function Chart() {
    return (
        <ResponsiveContainer width={"100%"} height={300}>
          <LineChart data={dummy_data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" padding={{ left: 30, right: 30 }} />
            <YAxis domain={[-100, 100]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="Acceleration"
              stroke="#8884d8"
              activeDot={{ r: 8 }}
              name="Acceleration (%)"
            />
            <Line type="monotone" dataKey="PopularityChange" stroke="#82ca9d" name="Popularity Change (%)" />
          </LineChart>
        </ResponsiveContainer>
      );
}