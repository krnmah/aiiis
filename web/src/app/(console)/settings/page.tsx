"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useInvestigationStore } from "@/store/use-investigation-store";

const apiBase =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function SettingsPage() {
  const topK = useInvestigationStore((state) => state.topK);
  const setTopK = useInvestigationStore((state) => state.setTopK);

  return (
    <main className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Console Settings</CardTitle>
          <CardDescription>
            Shared parameters used across Incidents and Logs pages.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">API Base URL</label>
            <Input value={apiBase} readOnly />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Default Top K</label>
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
    </main>
  );
}
