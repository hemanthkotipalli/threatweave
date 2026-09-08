"use client";

/**
 * apps/web/components/auth/AuthGuard.tsx
 * --------------------------------------
 * Higher-order wrapper component for protected views (e.g. /investigations/new).
 * Redirects unauthenticated visitors to /login.
 *
 * NOTE: Demo Mode pages (/demo, /demo/*) MUST NOT be wrapped in AuthGuard.
 */

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { isAuthenticated } from "../../lib/auth";

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function AuthGuard({ children, fallback }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [authorized, setAuthorized] = useState<boolean>(false);


  useEffect(() => {
    const timer = setTimeout(() => {
      if (!isAuthenticated()) {
        const redirectUrl = pathname ? `/login?redirect=${encodeURIComponent(pathname)}` : "/login";
        router.push(redirectUrl);
      } else {
        setAuthorized(true);
      }
    }, 0);

    return () => clearTimeout(timer);
  }, [router, pathname]);

  if (!authorized) {
    if (fallback) return <>{fallback}</>;


    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center p-8 text-center">
        <div className="w-8 h-8 border-2 border-accent-primary border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-soc-text-secondary text-sm font-mono">
          Verifying security authorization...
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
