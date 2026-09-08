"use client";

import React from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Filter, X, Calendar } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface FilterBarProps {
  isLoading?: boolean;
}

export function FilterBar({ isLoading = false }: FilterBarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const currentStatus = searchParams.get("status") || "all";
  const currentSeverity = searchParams.get("severity") || "all";
  const currentDateFrom = searchParams.get("date_from") || "";
  const currentDateTo = searchParams.get("date_to") || "";

  const updateParam = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    // Reset page to 1 when filters change
    params.set("page", "1");
    if (!value || value === "all") {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  const hasActiveFilters =
    (currentStatus !== "all" && currentStatus !== "") ||
    (currentSeverity !== "all" && currentSeverity !== "") ||
    currentDateFrom !== "" ||
    currentDateTo !== "";

  const resetFilters = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("status");
    params.delete("severity");
    params.delete("date_from");
    params.delete("date_to");
    params.set("page", "1");
    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <div className="bg-soc-surface border border-soc-border rounded-lg p-4 mb-6 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Filters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 flex-grow">
          {/* Status Select */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="filter-status"
              className="text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider"
            >
              Status
            </label>
            <select
              id="filter-status"
              value={currentStatus}
              onChange={(e) => updateParam("status", e.target.value)}
              disabled={isLoading}
              className="bg-soc-base border border-soc-border rounded px-3 py-1.5 text-xs font-mono text-soc-text-primary focus:outline-none focus:border-accent-primary disabled:opacity-50"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {/* Severity Select */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="filter-severity"
              className="text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider"
            >
              Severity
            </label>
            <select
              id="filter-severity"
              value={currentSeverity}
              onChange={(e) => updateParam("severity", e.target.value)}
              disabled={isLoading}
              className="bg-soc-base border border-soc-border rounded px-3 py-1.5 text-xs font-mono text-soc-text-primary focus:outline-none focus:border-accent-primary disabled:opacity-50"
            >
              <option value="all">All Severities</option>
              <option value="info">Info</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          {/* Date From */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="filter-date-from"
              className="text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider flex items-center gap-1"
            >
              <Calendar className="h-3 w-3 text-soc-text-muted" />
              Date From
            </label>
            <input
              id="filter-date-from"
              type="date"
              value={currentDateFrom}
              onChange={(e) => updateParam("date_from", e.target.value)}
              disabled={isLoading}
              className="bg-soc-base border border-soc-border rounded px-3 py-1 text-xs font-mono text-soc-text-primary focus:outline-none focus:border-accent-primary disabled:opacity-50"
            />
          </div>

          {/* Date To */}
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="filter-date-to"
              className="text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider flex items-center gap-1"
            >
              <Calendar className="h-3 w-3 text-soc-text-muted" />
              Date To
            </label>
            <input
              id="filter-date-to"
              type="date"
              value={currentDateTo}
              onChange={(e) => updateParam("date_to", e.target.value)}
              disabled={isLoading}
              className="bg-soc-base border border-soc-border rounded px-3 py-1 text-xs font-mono text-soc-text-primary focus:outline-none focus:border-accent-primary disabled:opacity-50"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 self-end lg:self-center shrink-0 pt-2 lg:pt-0">
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={resetFilters}
              disabled={isLoading}
              className="text-xs font-mono text-soc-text-secondary hover:text-soc-text-primary h-8"
            >
              <X className="h-3.5 w-3.5 mr-1" />
              Reset Filters
            </Button>
          )}

          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 bg-soc-base border border-soc-border rounded text-xs font-mono text-soc-text-muted">
            <Filter className="h-3.5 w-3.5 text-accent-primary" />
            <span>URL-Synced</span>
          </div>
        </div>
      </div>
    </div>
  );
}
