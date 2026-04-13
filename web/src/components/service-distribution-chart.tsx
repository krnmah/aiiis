"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import { SimilarLogItem } from "@/lib/types";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

type Props = {
  logs: SimilarLogItem[];
};

export function ServiceDistributionChart({ logs }: Props) {
  const option = useMemo(() => {
    const counts = logs.reduce<Record<string, number>>((acc, log) => {
      acc[log.service_name] = (acc[log.service_name] ?? 0) + 1;
      return acc;
    }, {});

    const data = Object.entries(counts).map(([name, value]) => ({ name, value }));

    return {
      tooltip: {
        trigger: "item",
      },
      series: [
        {
          type: "pie",
          radius: ["45%", "75%"],
          data,
          label: {
            color: "#e8e8eb",
          },
          itemStyle: {
            borderRadius: 10,
            borderColor: "#17181b",
            borderWidth: 3,
          },
        },
      ],
    };
  }, [logs]);

  if (logs.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Chart appears after running similarity search.
      </div>
    );
  }

  return <ReactECharts option={option} style={{ height: 260 }} />;
}
