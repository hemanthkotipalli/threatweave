"use client";

import React from "react";
import Link from "next/link";
import {
  FileText,
  Globe,
  Image as ImageIcon,
  Mic,
  QrCode,
  ArrowUpRight,
  Printer,
  Clock,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { SeverityTag, SeverityType } from "@/components/ui/SeverityTag";
import { InvestigationListItem } from "@/lib/types";

interface InvestigationRowProps {
  item: InvestigationListItem;
}

export function InvestigationRow({ item }: InvestigationRowProps) {
  const isCompleted = item.status === "completed";
  const sev = item.final_severity as SeverityType | undefined;
  const modalities = item.modalities || [];

  const renderModalityIcon = (mod: string) => {
    switch (mod.toLowerCase()) {
      case "text":
        return (
          <span
            key={mod}
            title="Text Evidence"
            className="inline-flex items-center p-1 rounded bg-soc-base border border-soc-border text-soc-text-secondary"
          >
            <FileText className="h-3.5 w-3.5" />
          </span>
        );
      case "url":
        return (
          <span
            key={mod}
            title="URL Evidence"
            className="inline-flex items-center p-1 rounded bg-soc-base border border-soc-border text-accent-primary"
          >
            <Globe className="h-3.5 w-3.5" />
          </span>
        );
      case "image":
        return (
          <span
            key={mod}
            title="Image Evidence"
            className="inline-flex items-center p-1 rounded bg-soc-base border border-soc-border text-soc-text-primary"
          >
            <ImageIcon className="h-3.5 w-3.5" />
          </span>
        );
      case "qr":
        return (
          <span
            key={mod}
            title="QR Code Evidence"
            className="inline-flex items-center p-1 rounded bg-soc-base border border-soc-border text-accent-primary"
          >
            <QrCode className="h-3.5 w-3.5" />
          </span>
        );
      case "voice":
      case "audio":
        return (
          <span
            key={mod}
            title="Audio/Voice Evidence"
            className="inline-flex items-center p-1 rounded bg-soc-base border border-soc-border text-severity-medium"
          >
            <Mic className="h-3.5 w-3.5" />
          </span>
        );
      default:
        return (
          <span
            key={mod}
            title={mod}
            className="inline-flex items-center px-1.5 py-0.5 rounded bg-soc-base border border-soc-border text-[10px] font-mono text-soc-text-muted uppercase"
          >
            {mod}
          </span>
        );
    }
  };

  return (
    <div className="grid grid-cols-12 items-center px-5 py-4 hover:bg-soc-elevated/40 transition-colors group text-sm gap-2">
      {/* Title, ID & Modalities */}
      <div className="col-span-12 md:col-span-5 pr-2">
        <div className="flex items-center gap-2 mb-1">
          <Link
            href={`/investigations/${item.id}`}
            className="font-display font-medium text-soc-text-primary group-hover:text-accent-primary transition-colors truncate"
          >
            {item.title || "Untitled Threat Investigation"}
          </Link>
          <Link
            href={`/investigations/${item.id}`}
            aria-label="Open Workspace"
            className="text-soc-text-muted hover:text-accent-primary transition-colors shrink-0"
          >
            <ArrowUpRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
          </Link>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs font-mono text-soc-text-muted truncate">
            ID: {item.id}
          </span>

          {modalities.length > 0 && (
            <div className="flex items-center gap-1">
              {modalities.map((m) => renderModalityIcon(m))}
            </div>
          )}
        </div>
      </div>

      {/* Severity */}
      <div className="col-span-4 md:col-span-2">
        {sev ? (
          <SeverityTag severity={sev} />
        ) : (
          <Badge variant="outline" className="text-[11px] font-mono text-soc-text-muted">
            Pending Analysis
          </Badge>
        )}
      </div>

      {/* Status */}
      <div className="col-span-4 md:col-span-2">
        <Badge
          variant={
            item.status === "completed"
              ? "accent"
              : item.status === "failed"
              ? "outline"
              : "default"
          }
          className="text-[11px] font-mono uppercase"
        >
          {item.status}
        </Badge>
      </div>

      {/* Timestamp & Report Link */}
      <div className="col-span-4 md:col-span-3 flex items-center justify-end gap-3 text-right text-xs font-mono text-soc-text-muted">
        <span className="hidden sm:inline flex items-center gap-1">
          <Clock className="h-3 w-3 inline text-soc-text-muted" />
          {new Date(item.created_at).toLocaleDateString()}{" "}
          {new Date(item.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
        <span className="sm:hidden">
          {new Date(item.created_at).toLocaleDateString()}
        </span>

        {isCompleted && (
          <Link
            href={`/investigations/${item.id}/report`}
            title="View Executive Report"
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-soc-base border border-soc-border hover:border-accent-primary hover:text-accent-primary transition-colors text-[11px] font-mono text-soc-text-secondary shrink-0"
          >
            <Printer className="h-3 w-3" />
            <span className="hidden md:inline">Report</span>
          </Link>
        )}
      </div>
    </div>
  );
}
