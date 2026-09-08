"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Globe,
  Image as ImageIcon,
  Mic,
  Tag,
  AlertCircle,
  Loader2,
  ArrowRight,
  UploadCloud,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { createInvestigation, ApiError } from "@/lib/api";

export function UploadForm() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);

  const [validationError, setValidationError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);
    setApiError(null);

    // Client-side validation: must have at least one modality
    const hasText = text.trim().length > 0;
    const hasUrl = url.trim().length > 0;
    const hasImage = imageFile !== null;
    const hasVoice = voiceFile !== null;

    if (!hasText && !hasUrl && !hasImage && !hasVoice) {
      setValidationError(
        "At least one evidence modality (Text, URL, Image, or Audio) must be provided to initiate an investigation."
      );
      return;
    }

    const formData = new FormData();
    if (title.trim()) {
      formData.append("title", title.trim());
    }
    if (hasText) {
      formData.append("text", text.trim());
    }
    if (hasUrl) {
      formData.append("url", url.trim());
    }
    if (imageFile) {
      formData.append("image", imageFile);
    }
    if (voiceFile) {
      formData.append("voice", voiceFile);
    }

    setIsSubmitting(true);
    try {
      const response = await createInvestigation(formData);
      const invId = response.investigation.id;
      router.push(`/investigations/${invId}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError(err.message);
      } else {
        setApiError("An unexpected error occurred while creating the investigation.");
      }
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="max-w-3xl mx-auto w-full border-soc-border bg-soc-surface p-6 sm:p-8">
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {/* Title input */}
        <div>
          <label
            htmlFor="inv-title"
            className="flex items-center gap-2 text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider mb-2"
          >
            <Tag className="h-3.5 w-3.5 text-accent-primary" />
            Investigation Title (Optional)
          </label>
          <input
            id="inv-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Suspected SBI Phishing Lure & Malicious APK Landing Page"
            className="w-full bg-soc-base border border-soc-border rounded-md px-3.5 py-2.5 text-sm text-soc-text-primary placeholder:text-soc-text-muted focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-colors"
          />
        </div>

        {/* Text Modality */}
        <div>
          <label
            htmlFor="inv-text"
            className="flex items-center gap-2 text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider mb-2"
          >
            <FileText className="h-3.5 w-3.5 text-severity-info" />
            Raw Text / Message Payload
          </label>
          <textarea
            id="inv-text"
            rows={4}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="Paste suspicious SMS text, WhatsApp message, email body, extortion script, or threat note..."
            className="w-full bg-soc-base border border-soc-border rounded-md px-3.5 py-2.5 text-sm text-soc-text-primary placeholder:text-soc-text-muted focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-colors font-mono leading-relaxed"
          />
        </div>

        {/* URL Modality */}
        <div>
          <label
            htmlFor="inv-url"
            className="flex items-center gap-2 text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider mb-2"
          >
            <Globe className="h-3.5 w-3.5 text-severity-medium" />
            Target URL / Domain
          </label>
          <input
            id="inv-url"
            type="url"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="e.g., http://192.168.1.100/sbi-verify/login.php or https://bit.ly/claim-prize"
            className="w-full bg-soc-base border border-soc-border rounded-md px-3.5 py-2.5 text-sm text-soc-text-primary placeholder:text-soc-text-muted focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-colors font-mono"
          />
        </div>

        {/* Image and Audio File Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Image Input */}
          <div className="border border-soc-border rounded-md p-4 bg-soc-base/40">
            <label className="flex items-center gap-2 text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider mb-3">
              <ImageIcon className="h-3.5 w-3.5 text-severity-low" />
              Image / QR Evidence
            </label>
            {imageFile ? (
              <div className="flex items-center justify-between bg-soc-elevated border border-soc-border/60 rounded px-3 py-2">
                <span className="text-xs font-mono text-soc-text-primary truncate max-w-[180px]">
                  {imageFile.name}
                </span>
                <button
                  type="button"
                  onClick={() => setImageFile(null)}
                  className="text-soc-text-muted hover:text-severity-critical transition-colors p-1"
                  aria-label="Remove image file"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center border border-dashed border-soc-border hover:border-accent-primary/60 rounded p-4 cursor-pointer transition-colors bg-soc-base/60">
                <UploadCloud className="h-6 w-6 text-soc-text-muted mb-1" />
                <span className="text-xs font-medium text-soc-text-secondary">Upload screenshot / QR</span>
                <span className="text-[10px] font-mono text-soc-text-muted mt-0.5">PNG, JPG, WebP up to 10MB</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setImageFile(e.target.files[0]);
                      if (validationError) setValidationError(null);
                    }
                  }}
                  className="hidden"
                />
              </label>
            )}
          </div>

          {/* Voice Input */}
          <div className="border border-soc-border rounded-md p-4 bg-soc-base/40">
            <label className="flex items-center gap-2 text-xs font-mono font-medium text-soc-text-secondary uppercase tracking-wider mb-3">
              <Mic className="h-3.5 w-3.5 text-severity-high" />
              Audio / Voice Evidence
            </label>
            {voiceFile ? (
              <div className="flex items-center justify-between bg-soc-elevated border border-soc-border/60 rounded px-3 py-2">
                <span className="text-xs font-mono text-soc-text-primary truncate max-w-[180px]">
                  {voiceFile.name}
                </span>
                <button
                  type="button"
                  onClick={() => setVoiceFile(null)}
                  className="text-soc-text-muted hover:text-severity-critical transition-colors p-1"
                  aria-label="Remove audio file"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center border border-dashed border-soc-border hover:border-accent-primary/60 rounded p-4 cursor-pointer transition-colors bg-soc-base/60">
                <UploadCloud className="h-6 w-6 text-soc-text-muted mb-1" />
                <span className="text-xs font-medium text-soc-text-secondary">Upload audio / voicemail</span>
                <span className="text-[10px] font-mono text-soc-text-muted mt-0.5">WAV, MP3, OGG up to 15MB</span>
                <input
                  type="file"
                  accept="audio/*"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setVoiceFile(e.target.files[0]);
                      if (validationError) setValidationError(null);
                    }
                  }}
                  className="hidden"
                />
              </label>
            )}
          </div>
        </div>

        {/* Validation Error Notice */}
        {validationError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded border border-severity-critical/30 bg-severity-critical/10 p-3.5 text-xs text-severity-critical"
          >
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{validationError}</p>
          </div>
        )}

        {/* API Error Notice */}
        {apiError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded border border-severity-critical/30 bg-severity-critical/10 p-3.5 text-xs text-severity-critical"
          >
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Submission Failed: </span>
              <span>{apiError}</span>
            </div>
          </div>
        )}

        {/* Submit Actions */}
        <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-between gap-3 pt-4 border-t border-soc-border">
          <Button
            type="button"
            variant="ghost"
            size="md"
            onClick={() => router.push("/investigations")}
            disabled={isSubmitting}
          >
            Cancel
          </Button>

          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={isSubmitting}
            className="w-full sm:w-auto min-w-[200px]"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Ingesting Artifacts...
              </>
            ) : (
              <>
                Create Investigation
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}
