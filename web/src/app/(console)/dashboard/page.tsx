"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot, DatabaseZap, HeartPulse, Radar } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getDbHealth, getHealth } from "@/lib/api";

export default function DashboardPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth, refetchInterval: 15000 });
  const dbHealth = useQuery({
    queryKey: ["health", "db"],
    queryFn: getDbHealth,
    refetchInterval: 15000,
  });

  return (
    <main className="space-y-5">
      <section className="rounded-3xl border border-border bg-[linear-gradient(125deg,#201113_0%,#121214_45%,#0f0f10_100%)] p-6 shadow-[0_20px_45px_-30px_rgba(0,0,0,0.95)]">
        <p className="text-xs uppercase tracking-[0.18em] text-[#ff8a8a]">Mission Status</p>
        <h2 className="mt-2 text-3xl font-semibold text-[#ffecef]">Operations Dashboard</h2>
        <p className="mt-3 max-w-2xl text-sm text-[#d6cec7]">
          Monitor API health, backend stability, and AI processing readiness from one
          console.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="API Health"
          value={health.data?.status ?? "checking"}
          description="Service heartbeat"
          icon={<HeartPulse className="h-4 w-4" />}
        />
        <MetricCard
          title="Database"
          value={dbHealth.data?.database ?? "checking"}
          description="Postgres availability"
          icon={<DatabaseZap className="h-4 w-4" />}
        />
        <MetricCard
          title="Inference"
          value="active"
          description="LLM routes reachable"
          icon={<Bot className="h-4 w-4" />}
        />
        <MetricCard
          title="Telemetry"
          value="online"
          description="Metrics stream enabled"
          icon={<Radar className="h-4 w-4" />}
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Analyze Incident</CardTitle>
            <CardDescription>
              Run AI-assisted incident analysis and get root cause with evidence,
              confidence, and next checks.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <Link href="/incidents" className={buttonVariants({ variant: "default" })}>
              Go To Incidents
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Logs Search</CardTitle>
            <CardDescription>
              Find semantically similar logs for a query and inspect result distribution
              before deeper analysis.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <Link href="/logs" className={buttonVariants({ variant: "default" })}>
              Go To Logs
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Enter New Logs</CardTitle>
            <CardDescription>
              Submit new log events manually to the backend ingestion pipeline for
              immediate availability.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <Link href="/post-logs" className={buttonVariants({ variant: "default" })}>
              Go To Post Logs
            </Link>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

function MetricCard({
  title,
  value,
  description,
  icon,
}: {
  title: string;
  value: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription className="flex items-center gap-2 text-[#ff8a8a]">
          {icon}
          {title}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-semibold capitalize">{value}</p>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}
