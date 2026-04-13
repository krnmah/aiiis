"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ServiceDistributionChart } from "@/components/service-distribution-chart";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getSimilarLogs } from "@/lib/api";
import { useInvestigationStore } from "@/store/use-investigation-store";

export default function LogsPage() {
  const query = useInvestigationStore((state) => state.query);
  const topK = useInvestigationStore((state) => state.topK);
  const setQuery = useInvestigationStore((state) => state.setQuery);
  const setTopK = useInvestigationStore((state) => state.setTopK);
  const [liveQuery, setLiveQuery] = useState(query);
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(liveQuery);
    }, 1000);

    return () => clearTimeout(timer);
  }, [liveQuery]);

  const similarLogs = useQuery({
    queryKey: ["similar-logs", debouncedQuery, topK],
    queryFn: () => getSimilarLogs(debouncedQuery, topK),
    enabled: debouncedQuery.trim().length > 2,
  });

  return (
    <main className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Similar Logs Search</CardTitle>
          <CardDescription>
            Explore semantic matches from your current investigation query.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">Query</label>
            <Input
              value={liveQuery}
              onChange={(event) => {
                const value = event.target.value;
                setLiveQuery(value);
                setQuery(value);
              }}
              placeholder="checkout latency spike"
            />
            <p className="text-xs text-muted-foreground">
              Search runs after 1 second of no typing.
            </p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Top K</label>
            <Input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(event) => {
                const value = Number(event.target.value || "1");
                setTopK(Math.max(1, Math.min(20, value)));
              }}
            />
          </div>
        </CardContent>
      </Card>

      <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Service Distribution</CardTitle>
            <CardDescription>Breakdown of top similar logs by service.</CardDescription>
          </CardHeader>
          <CardContent>
            <ServiceDistributionChart logs={similarLogs.data?.results ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Result Summary</CardTitle>
            <CardDescription>Quick stats for current retrieval output.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>Total results: {similarLogs.data?.total ?? 0}</p>
            <p className="text-muted-foreground">
              {similarLogs.isPending
                ? "Loading logs after typing pause..."
                : "Similarity scores are cosine-based."}
            </p>
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Top Similar Logs</CardTitle>
          <CardDescription>Live response from /logs/similar.</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-muted-foreground">
                <th className="px-2 py-2 font-medium">Service</th>
                <th className="px-2 py-2 font-medium">Level</th>
                <th className="px-2 py-2 font-medium">Message</th>
                <th className="px-2 py-2 font-medium">Score</th>
              </tr>
            </thead>
            <tbody>
              {(similarLogs.data?.results ?? []).map((log) => (
                <tr key={log.id} className="border-b border-border/70">
                  <td className="px-2 py-3 font-medium">{log.service_name}</td>
                  <td className="px-2 py-3">
                    <LevelBadge level={log.level} />
                  </td>
                  <td className="px-2 py-3 text-muted-foreground">{log.message}</td>
                  <td className="px-2 py-3 font-mono">{log.similarity_score.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </main>
  );
}

function LevelBadge({ level }: { level: string }) {
  const normalized = level.toUpperCase();
  if (normalized === "CRITICAL" || normalized === "ERROR") {
    return <Badge variant="danger">{level}</Badge>;
  }
  if (normalized === "WARNING") {
    return <Badge variant="warning">{level}</Badge>;
  }
  if (normalized === "INFO") {
    return <Badge variant="default">{level}</Badge>;
  }
  return <Badge variant="muted">{level}</Badge>;
}
