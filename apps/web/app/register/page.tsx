"use client";

/**
 * apps/web/app/register/page.tsx
 * ------------------------------
 * Analyst registration page utilizing Phase 1 design system components.
 * Registers user with POST /api/v1/auth/register, logs in, and redirects to dashboard.
 */

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { loginUser, registerUser } from "../../lib/auth";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTarget = searchParams.get("redirect") || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      // 1. Register user
      await registerUser({ email: email.trim(), password });

      // 2. Automatically authenticate and store token
      await loginUser({ email: email.trim(), password });

      // 3. Redirect to destination
      router.push(redirectTarget);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-soc-base text-soc-text-primary flex flex-col justify-center items-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Header Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-primary/10 border border-accent-primary/30 text-accent-primary text-xs font-mono mb-4">
            <span className="w-2 h-2 rounded-full bg-accent-primary animate-pulse" />
            ANALYST ONBOARDING
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-soc-text-primary font-display">
            Register SOC Analyst
          </h1>
          <p className="text-sm text-soc-text-secondary mt-1">
            Create an authenticated account for threat investigations
          </p>
        </div>

        {/* Register Card */}
        <Card className="p-6 sm:p-8 bg-soc-surface border border-soc-border shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div
                id="register-error-banner"
                className="p-3 bg-severity-critical/10 border border-severity-critical/30 rounded text-severity-critical text-xs font-mono"
              >
                {error}
              </div>
            )}

            <div>
              <label
                htmlFor="register-email"
                className="block text-xs font-mono uppercase tracking-wider text-soc-text-secondary mb-2"
              >
                Analyst Email
              </label>
              <input
                id="register-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@threatweave.local"
                className="w-full px-3 py-2.5 bg-soc-base border border-soc-border rounded text-sm text-soc-text-primary placeholder:text-soc-text-secondary/50 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-colors font-mono"
              />
            </div>

            <div>
              <label
                htmlFor="register-password"
                className="block text-xs font-mono uppercase tracking-wider text-soc-text-secondary mb-2"
              >
                Password (min 6 characters)
              </label>
              <input
                id="register-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2.5 bg-soc-base border border-soc-border rounded text-sm text-soc-text-primary placeholder:text-soc-text-secondary/50 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-colors font-mono"
              />
            </div>

            <div>
              <label
                htmlFor="register-confirm-password"
                className="block text-xs font-mono uppercase tracking-wider text-soc-text-secondary mb-2"
              >
                Confirm Password
              </label>
              <input
                id="register-confirm-password"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2.5 bg-soc-base border border-soc-border rounded text-sm text-soc-text-primary placeholder:text-soc-text-secondary/50 focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-colors font-mono"
              />
            </div>

            <Button
              id="register-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full justify-center mt-2"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Creating Account...
                </span>
              ) : (
                "Complete Registration"
              )}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-soc-border text-center text-xs text-soc-text-secondary">
            Already have an account?{" "}
            <a
              href="/login"
              className="text-accent-primary hover:underline font-medium"
            >
              Sign In
            </a>
          </div>
        </Card>

        {/* Demo Mode Notice */}
        <div className="mt-6 p-4 rounded-lg bg-soc-surface/50 border border-soc-border/60 text-center">
          <p className="text-xs text-soc-text-secondary mb-2">
            No registration needed to evaluate the platform.
          </p>
          <a
            href="/demo"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-accent-primary hover:text-accent-hover hover:underline"
          >
            Launch Open Demo Mode &rarr;
          </a>
        </div>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-soc-base flex items-center justify-center text-sm text-soc-text-secondary">Loading registration...</div>}>
      <RegisterForm />
    </Suspense>
  );
}
