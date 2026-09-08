"use client";

import React, { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Layers,
  Plus,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { FilterBar } from "@/components/history/FilterBar";
import { InvestigationRow } from "@/components/history/InvestigationRow";
import { listInvestigations, ApiError } from "@/lib/api";
import { InvestigationListItem } from "@/lib/types";

function InvestigationsListContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [items, setItems] = useState<InvestigationListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const page = parseInt(searchParams.get("page") || "1", 10) || 1;
  const pageSize = 10;
  const status = searchParams.get("status") || undefined;
  const severity = searchParams.get("severity") || undefined;
  const dateFrom = searchParams.get("date_from") || undefined;
  const dateTo = searchParams.get("date_to") || undefined;

  const hasActiveFilters =
    Boolean(status && status !== "all") ||
    Boolean(severity && severity !== "all") ||
    Boolean(dateFrom) ||
    Boolean(dateTo);

  const fetchItems = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await listInvestigations(page, pageSize, {
        status,
        severity,
        date_from: dateFrom,
        date_to: dateTo,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to retrieve investigations queue.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, status, severity, dateFrom, dateTo]);

  useEffect(() => {
    let isMounted = true;
    void (async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await listInvestigations(page, pageSize, {
          status,
          severity,
          date_from: dateFrom,
          date_to: dateTo,
        });
        if (!isMounted) return;
        setItems(res.items);
        setTotal(res.total);
      } catch (err) {
        if (!isMounted) return;
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to retrieve investigations queue.");
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [page, pageSize, status, severity, dateFrom, dateTo]);

  const totalPages = Math.ceil(total / pageSize) || 1;

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(newPage));
    router.push(`/investigations?${params.toString()}`);
  };

  const handleResetFilters = () => {
    router.push("/investigations?page=1");
  };

  return (
    <div className="flex flex-col min-h-screen bg-soc-base text-soc-text-primary px-4 md:px-8 py-6 max-w-7xl mx-auto w-full">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-soc-border pb-6 mb-6">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <Layers className="h-5 w-5 text-accent-primary" />
            <h1 className="font-display font-bold text-xxl tracking-tight text-soc-text-primary">
              Investigation History
            </h1>
            <Badge variant="outline" className="font-mono text-xs">
              {total} {hasActiveFilters ? "Filtered" : "Total"}
            </Badge>
          </div>
          <p className="text-soc-text-secondary text-sm">
            Comprehensive audit log of multimodal threat investigations, severity classifications, and reports.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchItems}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => router.push("/investigations/new")}
          >
            <Plus className="h-4 w-4 mr-1.5" />
            New Investigation
          </Button>
        </div>
      </header>

      {/* Filter Bar */}
      <FilterBar isLoading={isLoading} />

      {/* Main Content */}
      <main className="flex-grow flex flex-col">
        {isLoading ? (
          <Card className="p-6 space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </Card>
        ) : error ? (
          <Card className="p-8 text-center border-severity-critical/30 bg-soc-surface">
            <p className="text-severity-critical text-sm mb-4 font-mono">{error}</p>
            <Button variant="secondary" size="sm" onClick={fetchItems}>
              Retry Connection
            </Button>
          </Card>
        ) : items.length === 0 ? (
          hasActiveFilters ? (
            <EmptyState
              title="No matching investigations"
              description="No investigations match the selected filters. Try broadening your criteria or resetting your search parameters."
              action={
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleResetFilters}
                >
                  <RotateCcw className="h-4 w-4 mr-1.5" />
                  Reset Active Filters
                </Button>
              }
            />
          ) : (
            <EmptyState
              title="No investigations found"
              description="No threat investigations have been initiated yet. Submit suspicious text, URLs, QR codes, or audio recordings to launch the agent swarm."
              action={
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => router.push("/investigations/new")}
                >
                  <Plus className="h-4 w-4 mr-1.5" />
                  Start First Investigation
                </Button>
              }
            />
          )
        ) : (
          <Card className="p-0 border-soc-border bg-soc-surface overflow-hidden flex flex-col flex-grow shadow-md">
            {/* Table Header */}
            <div className="grid grid-cols-12 bg-soc-base border-b border-soc-border px-5 py-3 text-xs font-mono text-soc-text-secondary uppercase tracking-wider font-semibold gap-2">
              <div className="col-span-12 md:col-span-5">Investigation / Modalities</div>
              <div className="col-span-4 md:col-span-2">Severity</div>
              <div className="col-span-4 md:col-span-2">Status</div>
              <div className="col-span-4 md:col-span-3 text-right">Created / Actions</div>
            </div>

            {/* Table Body */}
            <div className="divide-y divide-soc-border/60">
              {items.map((item) => (
                <InvestigationRow key={item.id} item={item} />
              ))}
            </div>

            {/* Pagination Footer */}
            <div className="flex items-center justify-between border-t border-soc-border px-5 py-3.5 bg-soc-base/40 text-xs font-mono text-soc-text-secondary mt-auto">
              <span>
                Page {page} of {totalPages} ({total} investigations)
              </span>

              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handlePageChange(Math.max(1, page - 1))}
                  disabled={page <= 1 || isLoading}
                  className="h-8 px-2.5"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handlePageChange(Math.min(totalPages, page + 1))}
                  disabled={page >= totalPages || isLoading}
                  className="h-8 px-2.5"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-soc-border pt-4 text-center">
        <p className="text-xs font-mono text-soc-text-muted">
          ThreatWeave Phase 14 — Multimodal Threat Intelligence & Audit History
        </p>
      </footer>
    </div>
  );
}

export default function InvestigationsListPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 max-w-7xl mx-auto">
          <Skeleton className="h-12 w-1/3 mb-6" />
          <Skeleton className="h-20 w-full mb-6" />
          <Skeleton className="h-64 w-full" />
        </div>
      }
    >
      <InvestigationsListContent />
    </Suspense>
  );
}
