"use client";

import { useMemo } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut, Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Filler,
  Tooltip,
  Legend,
);

const grid = "rgba(228, 219, 208, 0.9)";
const ink = "#2a241e";
const accent = "#c45c16";
const charcoal = "#1c1814";

const baseOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: charcoal,
      titleColor: "#fff",
      bodyColor: "#f3efe8",
      padding: 10,
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: "#6d645b", font: { size: 11 } },
      border: { color: grid },
    },
    y: {
      grid: { color: grid },
      ticks: { color: "#6d645b", font: { size: 11 } },
      border: { display: false },
    },
  },
};

export function LineChart({
  labels,
  values,
  label,
}: {
  labels: string[];
  values: number[];
  label: string;
}) {
  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          label,
          data: values,
          borderColor: accent,
          backgroundColor: "rgba(196, 92, 22, 0.12)",
          fill: true,
          tension: 0.35,
          pointRadius: 3,
          pointBackgroundColor: accent,
          borderWidth: 2,
        },
      ],
    }),
    [labels, values, label],
  );
  return (
    <div className="chart-wrap">
      <Line data={data} options={baseOptions} />
    </div>
  );
}

export function BarChart({
  labels,
  values,
  label,
}: {
  labels: string[];
  values: number[];
  label: string;
}) {
  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          label,
          data: values,
          backgroundColor: accent,
          borderRadius: 6,
          maxBarThickness: 28,
        },
      ],
    }),
    [labels, values, label],
  );
  return (
    <div className="chart-wrap">
      <Bar data={data} options={baseOptions} />
    </div>
  );
}

export function DoughnutChart({
  labels,
  values,
}: {
  labels: string[];
  values: number[];
}) {
  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: [accent, "#1c1814", "#cbb8a4"],
          borderWidth: 0,
        },
      ],
    }),
    [labels, values],
  );
  return (
    <div className="chart-wrap" style={{ height: 220 }}>
      <Doughnut
        data={data}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          cutout: "68%",
          plugins: {
            legend: {
              position: "bottom",
              labels: { color: ink, boxWidth: 10, font: { size: 12 } },
            },
          },
        }}
      />
    </div>
  );
}
