"use client";

import React, { useState, useEffect } from "react";
import {
  Tag,
  FileEdit,
  Bookmark,
  Download,
  Plus,
  Trash2,
  User,
  Clock,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { InvestigationDetail } from "@/lib/types";

export interface AnalystNote {
  id: string;
  author: string;
  content: string;
  createdAt: string;
}

export type TriageStatus =
  | "New / Ingested"
  | "In Triage"
  | "Escalated to Tier-2"
  | "Closed — True Positive"
  | "Closed — False Positive";

interface Props {
  investigation: InvestigationDetail;
  bookmarkedIds: string[];
  onToggleFilterBookmarks: () => void;
  isFilterBookmarksActive: boolean;
  className?: string;
}

export function AnalystWorkflowBar({
  investigation,
  bookmarkedIds,
  onToggleFilterBookmarks,
  isFilterBookmarksActive,
  className = "",
}: Props) {
  const storageKey = `threatweave:analyst:${investigation.id}`;

  const [triageStatus, setTriageStatus] = useState<TriageStatus>("In Triage");
  const [tags, setTags] = useState<string[]>([
    investigation.final_severity === "critical" || investigation.final_severity === "high"
      ? "Threat Confirmed"
      : "Automated Audit",
  ]);
  const [newTagInput, setNewTagInput] = useState<string>("");
  const [notes, setNotes] = useState<AnalystNote[]>([]);
  const [newNoteInput, setNewNoteInput] = useState<string>("");
  const [isNotesOpen, setIsNotesOpen] = useState<boolean>(false);

  // Load from localStorage safely
  useEffect(() => {
    let isMounted = true;
    const loadSaved = () => {
      try {
        const saved = localStorage.getItem(storageKey);
        if (saved && isMounted) {
          const parsed = JSON.parse(saved);
          if (parsed.triageStatus) setTriageStatus(parsed.triageStatus);
          if (Array.isArray(parsed.tags)) setTags(parsed.tags);
          if (Array.isArray(parsed.notes)) setNotes(parsed.notes);
        }
      } catch {
        // Fallback to default
      }
    };
    void Promise.resolve().then(loadSaved);
    return () => {
      isMounted = false;
    };
  }, [storageKey]);

  // Save to localStorage on changes
  const saveState = (updatedTags: string[], updatedNotes: AnalystNote[], updatedStatus: TriageStatus) => {
    try {
      localStorage.setItem(
        storageKey,
        JSON.stringify({
          triageStatus: updatedStatus,
          tags: updatedTags,
          notes: updatedNotes,
        })
      );
    } catch {
      // localStorage error handled silently
    }
  };

  const handleStatusChange = (newStatus: TriageStatus) => {
    setTriageStatus(newStatus);
    saveState(tags, notes, newStatus);
  };

  const handleAddTag = (tagToAdd: string) => {
    const trimmed = tagToAdd.trim();
    if (!trimmed || tags.includes(trimmed)) return;
    const updated = [...tags, trimmed];
    setTags(updated);
    setNewTagInput("");
    saveState(updated, notes, triageStatus);
  };

  const handleRemoveTag = (tagToRemove: string) => {
    const updated = tags.filter((t) => t !== tagToRemove);
    setTags(updated);
    saveState(updated, notes, triageStatus);
  };

  const handleAddNote = () => {
    if (!newNoteInput.trim()) return;
    const newNote: AnalystNote = {
      id: `note-${Date.now()}`,
      author: "SOC Analyst (Current User)",
      content: newNoteInput.trim(),
      createdAt: new Date().toISOString(),
    };
    const updated = [newNote, ...notes];
    setNotes(updated);
    setNewNoteInput("");
    saveState(tags, updated, triageStatus);
  };

  const handleDeleteNote = (noteId: string) => {
    const updated = notes.filter((n) => n.id !== noteId);
    setNotes(updated);
    saveState(tags, updated, triageStatus);
  };

  // Export Complete Case File as JSON
  const handleExportJson = () => {
    const caseData = {
      threatweave_investigation: {
        id: investigation.id,
        title: investigation.title,
        status: investigation.status,
        triage_status: triageStatus,
        created_at: investigation.created_at,
        completed_at: investigation.completed_at,
        final_risk_score: investigation.final_risk_score,
        final_severity: investigation.final_severity,
        final_confidence: investigation.final_confidence,
      },
      analyst_tags: tags,
      analyst_notes: notes,
      bookmarked_findings_count: bookmarkedIds.length,
      evidence_inputs: investigation.evidence_inputs,
      agent_runs: investigation.agent_runs,
      rag_citations: investigation.rag_citations,
      risk_breakdown: investigation.risk?.breakdown,
      conflict_arbitration: investigation.risk?.conflicts,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(caseData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `threatweave-case-${investigation.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className={`p-4 md:p-5 border-soc-border bg-soc-surface ${className}`}>
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Triage Status & Bookmarks */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Triage Status Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-soc-text-muted uppercase">
              Triage:
            </span>
            <select
              value={triageStatus}
              onChange={(e) => handleStatusChange(e.target.value as TriageStatus)}
              className="bg-soc-base border border-soc-border text-xs font-mono text-soc-text-primary px-2.5 py-1 rounded focus:outline-none focus:border-accent-primary"
            >
              <option value="New / Ingested">New / Ingested</option>
              <option value="In Triage">In Triage</option>
              <option value="Escalated to Tier-2">Escalated to Tier-2</option>
              <option value="Closed — True Positive">Closed — True Positive</option>
              <option value="Closed — False Positive">Closed — False Positive</option>
            </select>
          </div>

          {/* Bookmarked Filter Pill */}
          <button
            type="button"
            onClick={onToggleFilterBookmarks}
            className={`px-2.5 py-1 rounded text-xs font-mono flex items-center gap-1.5 transition-colors border ${
              isFilterBookmarksActive
                ? "bg-accent-primary text-white border-accent-primary font-bold"
                : "bg-soc-base border-soc-border text-soc-text-secondary hover:text-soc-text-primary"
            }`}
          >
            <Bookmark className="h-3 w-3" />
            <span>Bookmarked IOCs ({bookmarkedIds.length})</span>
          </button>

          {/* Notes Toggle Button */}
          <button
            type="button"
            onClick={() => setIsNotesOpen(!isNotesOpen)}
            className={`px-2.5 py-1 rounded text-xs font-mono flex items-center gap-1.5 transition-colors border ${
              isNotesOpen
                ? "bg-soc-base border-accent-primary text-accent-primary font-bold"
                : "bg-soc-base border-soc-border text-soc-text-secondary hover:text-soc-text-primary"
            }`}
          >
            <FileEdit className="h-3 w-3" />
            <span>Analyst Notes ({notes.length})</span>
          </button>
        </div>

        {/* Right: Tag bar and JSON Export */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Tag List */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <Tag className="h-3.5 w-3.5 text-soc-text-muted" />
            {tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-soc-base border border-soc-border text-[11px] font-mono text-soc-text-primary"
              >
                <span>{tag}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="text-soc-text-muted hover:text-severity-critical"
                >
                  &times;
                </button>
              </span>
            ))}

            {/* Quick Add Tag Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAddTag(newTagInput);
              }}
              className="inline-flex items-center"
            >
              <input
                type="text"
                value={newTagInput}
                onChange={(e) => setNewTagInput(e.target.value)}
                placeholder="+ Tag"
                className="w-16 focus:w-28 transition-all bg-soc-base border border-soc-border rounded px-1.5 py-0.5 text-[11px] font-mono text-soc-text-primary placeholder:text-soc-text-muted focus:outline-none focus:border-accent-primary"
              />
            </form>
          </div>

          {/* Export JSON Action */}
          <Button
            variant="secondary"
            size="sm"
            onClick={handleExportJson}
            title="Download full machine-readable JSON dossier"
            className="text-xs font-mono"
          >
            <Download className="h-3 w-3 mr-1" />
            Export JSON Case
          </Button>
        </div>
      </div>

      {/* Expandable Analyst Notes Drawer */}
      {isNotesOpen && (
        <div className="mt-4 pt-4 border-t border-soc-border/70 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-display font-semibold text-xs uppercase tracking-wider text-soc-text-primary">
              Incident Case Notes & Analyst Log
            </h4>
            <span className="text-[10px] font-mono text-soc-text-muted">
              Auto-persisted locally in browser (client-side only)
            </span>
          </div>

          {/* New Note Form */}
          <div className="flex gap-2">
            <textarea
              value={newNoteInput}
              onChange={(e) => setNewNoteInput(e.target.value)}
              placeholder="Add analytical observation, ticket cross-reference (e.g. JIRA-4029), or remediation instruction..."
              rows={2}
              className="w-full bg-soc-base border border-soc-border rounded p-2 text-xs font-mono text-soc-text-primary placeholder:text-soc-text-muted focus:outline-none focus:border-accent-primary"
            />
            <Button
              variant="primary"
              size="sm"
              onClick={handleAddNote}
              disabled={!newNoteInput.trim()}
              className="shrink-0 self-end"
            >
              <Plus className="h-3.5 w-3.5 mr-1" /> Add Note
            </Button>
          </div>

          {/* Notes Stream */}
          {notes.length === 0 ? (
            <p className="text-xs font-mono text-soc-text-muted italic">
              No analyst notes recorded yet for this case.
            </p>
          ) : (
            <div className="space-y-2">
              {notes.map((note) => (
                <div
                  key={note.id}
                  className="p-3 rounded bg-soc-base border border-soc-border flex items-start justify-between gap-3 text-xs font-mono"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-[10px] text-soc-text-muted">
                      <span className="flex items-center gap-1 font-bold text-accent-primary">
                        <User className="h-2.5 w-2.5" />
                        {note.author}
                      </span>
                      <span>&bull;</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-2.5 w-2.5" />
                        {new Date(note.createdAt).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-soc-text-primary leading-relaxed whitespace-pre-wrap">
                      {note.content}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteNote(note.id)}
                    className="text-soc-text-muted hover:text-severity-critical p-1"
                    title="Delete note"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
