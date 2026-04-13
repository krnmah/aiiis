"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createLog } from "@/lib/api";

type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

const levels: LogLevel[] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

export default function PostLogsPage() {
  const [serviceName, setServiceName] = useState("");
  const [level, setLevel] = useState<LogLevel>("ERROR");
  const [message, setMessage] = useState("");
  const [traceId, setTraceId] = useState("");

  const postLog = useMutation({
    mutationFn: () =>
      createLog({
        service_name: serviceName.trim(),
        level,
        message: message.trim(),
        trace_id: traceId.trim() || null,
      }),
    onSuccess: () => {
      setMessage("");
      setTraceId("");
    },
  });

  const canSubmit = serviceName.trim().length > 0 && message.trim().length > 0;

  return (
    <main className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Post New Log</CardTitle>
          <CardDescription>
            Send a new log event to the backend ingestion endpoint.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Service Name</label>
            <Input
              value={serviceName}
              onChange={(event) => setServiceName(event.target.value)}
              placeholder="payment-service"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Level</label>
            <select
              value={level}
              onChange={(event) => setLevel(event.target.value as LogLevel)}
              className="h-10 w-full rounded-xl border border-border bg-[#0f1012] px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              {levels.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Message</label>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Timeout while calling downstream inventory service"
              rows={5}
              className="w-full rounded-xl border border-border bg-[#0f1012] px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Trace ID (optional)</label>
            <Input
              value={traceId}
              onChange={(event) => setTraceId(event.target.value)}
              placeholder="trace-9f3cd1"
            />
          </div>

          <Button
            onClick={() => postLog.mutate()}
            disabled={postLog.isPending || !canSubmit}
            type="button"
          >
            {postLog.isPending ? "Posting..." : "Post Log"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Submission Result</CardTitle>
          <CardDescription>Response from POST /logs.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {postLog.error && (
            <p className="text-danger">Unable to post log. Please verify your input.</p>
          )}
          {postLog.data && (
            <div className="rounded-xl border border-border bg-[#101114] p-4 text-muted-foreground">
              <p>
                Created log <span className="font-mono text-foreground">#{postLog.data.id}</span>
              </p>
              <p>Service: {postLog.data.service_name}</p>
              <p>Level: {postLog.data.level}</p>
              <p>Trace ID: {postLog.data.trace_id ?? "none"}</p>
              <p>Timestamp: {new Date(postLog.data.timestamp).toLocaleString()}</p>
            </div>
          )}
          {!postLog.data && !postLog.error && (
            <p className="text-muted-foreground">No submission yet.</p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
