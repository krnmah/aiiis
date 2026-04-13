"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { analyzeIncident } from "@/lib/api";
import { useInvestigationStore } from "@/store/use-investigation-store";

type ParsedIncidentResponse = {
  rootCause: string;
  evidence: string[];
  confidence: string;
  nextChecks: string[];
};

function extractLogIds(text: string): number[] {
  const matches = text.match(/log_id\s*=\s*(\d+)/gi) ?? [];
  const ids = matches
    .map((part) => Number(part.replace(/\D+/g, "")))
    .filter((value) => Number.isFinite(value) && value > 0);
  return [...new Set(ids)];
}

function parseIncidentResponse(raw: string): ParsedIncidentResponse {
  const normalized = raw.replace(/\r\n/g, "\n").trim();

  const extract = (label: string, next: string[]): string => {
    const pattern =
      next.length > 0
        ? new RegExp(
            `${label}:\\s*([\\s\\S]*?)(?=\\n(?:${next.join("|")}):|$)`,
            "i",
          )
        : new RegExp(`${label}:\\s*([\\s\\S]*)$`, "i");
    const match = normalized.match(pattern);
    return (match?.[1] ?? "").trim();
  };

  const extractList = (value: string): string[] => {
    return value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => line.replace(/^-\s*/, ""));
  };

  const rootCause = extract("ROOT_CAUSE", ["EVIDENCE", "CONFIDENCE", "NEXT_CHECKS"]);
  const evidence = extractList(extract("EVIDENCE", ["CONFIDENCE", "NEXT_CHECKS"]));
  const confidence = extract("CONFIDENCE", ["NEXT_CHECKS"]);
  const nextChecks = extractList(extract("NEXT_CHECKS", []));

  return {
    rootCause: rootCause || normalized,
    evidence,
    confidence: confidence || "unknown",
    nextChecks,
  };
}

export default function IncidentsPage() {
  const query = useInvestigationStore((state) => state.query);
  const topK = useInvestigationStore((state) => state.topK);
  const setQuery = useInvestigationStore((state) => state.setQuery);
  const setTopK = useInvestigationStore((state) => state.setTopK);

  const incident = useMutation({
    mutationFn: () => analyzeIncident(query, topK),
  });

  const parsedIncident = incident.data
    ? parseIncidentResponse(incident.data.root_cause)
    : null;
  const evidenceLogIds = incident.data ? extractLogIds(incident.data.root_cause) : [];

  return (
    <main className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Incident Analysis</CardTitle>
          <CardDescription>
            Submit an investigation query to get structured AI root-cause output.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Query</label>
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="payment timeout during checkout"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Top K Logs</label>
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
          <Button onClick={() => incident.mutate()} disabled={incident.isPending || !query.trim()}>
            {incident.isPending ? "Analyzing..." : "Analyze Incident"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Output</CardTitle>
          <CardDescription>Result from the backend /incidents endpoint.</CardDescription>
        </CardHeader>
        <CardContent>
          {incident.isPending && <p className="text-sm text-muted-foreground">Running analysis...</p>}
          {incident.error && (
            <p className="text-sm text-danger">Incident analysis request failed.</p>
          )}
          {incident.data && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Analyzed logs: {incident.data.analyzed_log_count}
              </p>
              {evidenceLogIds.length > 0 && (
                <div className="rounded-xl border border-border bg-[#101114] p-4">
                  <h3 className="text-sm font-semibold text-[#ff8a8a]">LOG IDS IN EVIDENCE</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {evidenceLogIds.map((id) => (
                      <Link
                        key={`log-ref-${id}`}
                        href={`/log-details?logId=${id}`}
                        className="rounded-lg border border-border px-2 py-1 text-xs text-[#ff8a8a] hover:bg-[#231114]"
                      >
                        log_id={id}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
              {parsedIncident && (
                <div className="grid gap-3">
                  <article className="rounded-xl border border-border bg-[#101114] p-4">
                    <h3 className="text-sm font-semibold text-[#ff8a8a]">ROOT_CAUSE</h3>
                    <p className="mt-2 text-sm leading-relaxed">{parsedIncident.rootCause}</p>
                  </article>

                  <article className="rounded-xl border border-border bg-[#101114] p-4">
                    <h3 className="text-sm font-semibold text-[#ff8a8a]">EVIDENCE</h3>
                    {parsedIncident.evidence.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-sm leading-relaxed text-muted-foreground">
                        {parsedIncident.evidence.map((item) => (
                          <li key={`evidence-${item}`}>- {item}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-sm text-muted-foreground">No evidence provided.</p>
                    )}
                  </article>

                  <article className="rounded-xl border border-border bg-[#101114] p-4">
                    <h3 className="text-sm font-semibold text-[#ff8a8a]">CONFIDENCE</h3>
                    <p className="mt-2 text-sm uppercase tracking-wide">{parsedIncident.confidence}</p>
                  </article>

                  <article className="rounded-xl border border-border bg-[#101114] p-4">
                    <h3 className="text-sm font-semibold text-[#ff8a8a]">NEXT_CHECKS</h3>
                    {parsedIncident.nextChecks.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-sm leading-relaxed text-muted-foreground">
                        {parsedIncident.nextChecks.map((item) => (
                          <li key={`next-${item}`}>- {item}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-2 text-sm text-muted-foreground">No checks suggested.</p>
                    )}
                  </article>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
