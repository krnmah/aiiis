"use client";

import {
  ChevronLeft,
  ChevronRight,
  FileSearch,
  Home,
  ListFilter,
  Menu,
  Search,
  SquarePen,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useInvestigationStore } from "@/store/use-investigation-store";

type Props = {
  children: ReactNode;
};

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/incidents", label: "Incidents", icon: FileSearch },
  { href: "/logs", label: "Logs", icon: ListFilter },
  { href: "/log-details", label: "Log Details", icon: Search },
  { href: "/post-logs", label: "Post Logs", icon: SquarePen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function ConsoleShell({ children }: Props) {
  const pathname = usePathname();
  const sidebarCollapsed = useInvestigationStore((state) => state.sidebarCollapsed);
  const setSidebarCollapsed = useInvestigationStore(
    (state) => state.setSidebarCollapsed,
  );

  const [mobileOpen, setMobileOpen] = useState(false);

  const pageTitle = useMemo(() => {
    const active = navItems.find((item) => pathname.startsWith(item.href));
    return active?.label ?? "Dashboard";
  }, [pathname]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 hidden border-r border-border bg-[#0b0b0c] transition-all duration-300 md:flex md:flex-col",
          sidebarCollapsed ? "w-20" : "w-72",
        )}
      >
        <div className="flex items-center justify-between border-b border-border px-3 py-4">
          <div className={cn("flex items-center gap-2", sidebarCollapsed && "mx-auto")}> 
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-[13px] font-bold text-accent-foreground">
              AI
            </span>
            {!sidebarCollapsed && (
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[#ff8a8a]">
                  Incident Ops
                </p>
                <p className="text-sm font-semibold">Control Center</p>
              </div>
            )}
          </div>
          {!sidebarCollapsed && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSidebarCollapsed(true)}
              type="button"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          )}
          {sidebarCollapsed && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSidebarCollapsed(false)}
              type="button"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          )}
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[#2d1416] text-[#ff8a8a]"
                    : "text-[#cbcbcf] hover:bg-[#17171a] hover:text-[#ff8a8a]",
                  sidebarCollapsed && "justify-center px-2",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div
        className={cn(
          "transition-all duration-300",
          sidebarCollapsed ? "md:pl-20" : "md:pl-72",
        )}
      >
        <header className="sticky top-0 z-20 border-b border-border bg-[#101113]/85 px-4 py-3 backdrop-blur md:px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant="outline"
                className="md:hidden"
                onClick={() => setMobileOpen(true)}
                type="button"
              >
                <Menu className="h-4 w-4" />
              </Button>
              <h1 className="text-sm font-semibold uppercase tracking-[0.14em] text-[#ff8a8a]">
                {pageTitle}
              </h1>
            </div>
          </div>
        </header>

        <div className="px-4 py-6 md:px-6">{children}</div>
      </div>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            aria-label="Close menu"
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
            type="button"
          />
          <div className="absolute inset-y-0 left-0 w-72 border-r border-border bg-[#0b0b0c] p-3">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-[13px] font-bold text-accent-foreground">
                  AI
                </span>
                <p className="text-sm font-semibold">Control Center</p>
              </div>
              <Button size="sm" variant="outline" onClick={() => setMobileOpen(false)}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-[#2d1416] text-[#ff8a8a]"
                        : "text-[#cbcbcf] hover:bg-[#17171a] hover:text-[#ff8a8a]",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      )}
    </div>
  );
}
