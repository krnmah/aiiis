"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getLogDetail } from "@/lib/api";

export default function LogDetailsPage() {
  const [logIdInput, setLogIdInput] = useState("");

  const logDetail = useMutation({
    mutationFn: (logId: number) => getLogDetail(logId),
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("logId");
    if (!fromQuery) {
      return;
    }

    const parsed = Number(fromQuery);
    if (!Number.isNaN(parsed) && parsed > 0) {
      setLogIdInput(String(parsed));
      logDetail.mutate(parsed);
    }
    // intentionally run once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runLookup = () => {
    const parsed = Number(logIdInput);
    if (Number.isNaN(parsed) || parsed <= 0) {
      return;
    }
    logDetail.mutate(parsed);
  };

  return (
    <main className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Log Details By ID</CardTitle>
          <CardDescription>
            Enter a log ID from incident evidence and fetch complete log details.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Log ID</label>
            <Input
              type="number"
              min={1}
              value={logIdInput}
              onChange={(event) => setLogIdInput(event.target.value)}
              placeholder="42"
            />
          </div>
          <Button onClick={runLookup} disabled={logDetail.isPending || !logIdInput.trim()}>
            {logDetail.isPending ? "Fetching..." : "Get Log Details"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lookup Result</CardTitle>
          <CardDescription>Response from GET /logs/{'{'}log_id{'}'}.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {logDetail.error && (
            <p className="text-danger">Log not found or request failed.</p>
          )}

          {logDetail.data && (
            <div className="rounded-xl border border-border bg-[#101114] p-4 text-muted-foreground">
              <p>
                Log ID: <span className="font-mono text-foreground">{logDetail.data.id}</span>
              </p>
              <p>Service: {logDetail.data.service_name}</p>
              <p>Level: {logDetail.data.level}</p>
              <p>Trace ID: {logDetail.data.trace_id ?? "none"}</p>
              <p>Timestamp: {new Date(logDetail.data.timestamp).toLocaleString()}</p>
              <p className="mt-2 text-foreground">Message: {logDetail.data.message}</p>
            </div>
          )}

          {!logDetail.data && !logDetail.error && (
            <p className="text-muted-foreground">No lookup yet.</p>
          )}

          <p className="text-xs text-muted-foreground">
            Tip: From incidents page evidence, click a log ID link to open this page directly.
          </p>
          <Link href="/incidents" className="text-xs text-[#ff8a8a] underline-offset-2 hover:underline">
            Back to Incidents
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
