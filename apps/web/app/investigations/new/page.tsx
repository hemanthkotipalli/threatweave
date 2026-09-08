"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Shield } from "lucide-react";
import { UploadForm } from "@/components/investigation/UploadForm";
import { AuthGuard } from "@/components/auth/AuthGuard";

export default function NewInvestigationPage() {
  return (
    <AuthGuard>
      <div className="flex flex-col min-h-screen bg-soc-base text-soc-text-primary px-4 md:px-8 py-6 max-w-7xl mx-auto w-full">

      {/* Top Navigation Breadcrumb */}
      <div className="mb-6">
        <Link
          href="/investigations"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-soc-text-secondary hover:text-soc-text-primary transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Investigations Queue
        </Link>
      </div>

      {/* Header Banner */}
      <header className="border-b border-soc-border pb-6 mb-8">
        <div className="flex items-center gap-2.5 mb-1.5">
          <div className="p-1.5 rounded bg-accent-primary/10 border border-accent-primary/30 text-accent-primary">
            <Shield className="h-5 w-5" />
          </div>
          <h1 className="font-display font-bold text-xxl tracking-tight text-soc-text-primary">
            New Multimodal Threat Investigation
          </h1>
        </div>
        <p className="text-soc-text-secondary text-sm max-w-2xl leading-relaxed">
          Ingest raw threat artifacts across multiple channels — plain text messages, target URLs,
          suspicious QR codes or screenshots, and voice recordings. The ThreatWeave agent swarm will
          distribute analysis across specialized neural models.
        </p>
      </header>

      {/* Main Upload Form */}
      <main className="flex-grow flex items-start justify-center">
        <UploadForm />
      </main>

        {/* Footer */}
        <footer className="mt-12 border-t border-soc-border pt-4 text-center">
          <p className="text-xs font-mono text-soc-text-muted">
            ThreatWeave Phase 17 — Multimodal SOC Investigation Workspace
          </p>
        </footer>
      </div>
    </AuthGuard>
  );
}

