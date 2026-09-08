/**
 * apps/web/lib/auth.ts
 * --------------------
 * Client-side authentication helpers, token management, and authenticated fetch utility.
 *
 * ARCHITECTURE DECISION: LocalStorage vs httpOnly Cookies
 * --------------------------------------------------------
 * Decision: localStorage is chosen for client-side JWT token storage.
 *
 * Rationale & Tradeoffs:
 * - Environment: The Next.js frontend runs on localhost:3000 and directly issues
 *   client-side fetch requests to the FastAPI backend on localhost:8000 (cross-origin).
 * - Cross-Origin Cookies: Using httpOnly cookies across differing ports on localhost
 *   requires `SameSite=None; Secure`, which modern browsers reject on unencrypted HTTP.
 *   Alternatively, routing all requests through Next.js Route Handlers as a reverse proxy
 *   adds unnecessary complexity for this student capstone demonstration.
 * - Security Tradeoff: localStorage can be accessed by JavaScript running on the page,
 *   meaning any Cross-Site Scripting (XSS) vulnerability could leak the token. In contrast,
 *   httpOnly cookies cannot be read by client JavaScript, providing defense-in-depth against XSS
 *   (though requiring CSRF mitigations).
 * - Conclusion: For this educational prototype, storing the Bearer token in localStorage
 *   and attaching it explicitly via `Authorization: Bearer <token>` provides full transparency,
 *   reliable cross-origin communication, and simplicity without hidden proxy layers.
 */

import { AuthLoginPayload, AuthRegisterPayload, TokenResponse, UserProfile } from "./types";

const TOKEN_KEY = "threatweave_access_token";
const USER_KEY = "threatweave_user_profile";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:8000";

/**
 * Retrieves the stored JWT access token from localStorage.
 */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Persists the JWT access token in localStorage.
 */
export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Removes the stored JWT access token from localStorage.
 */
export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Retrieves the cached user profile from localStorage.
 */
export function getStoredUser(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
}

/**
 * Persists the user profile in localStorage.
 */
export function setStoredUser(user: UserProfile): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Clears all authentication state (token + user profile).
 */
export function clearAuth(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Returns true if a valid-looking token is present in localStorage.
 */
export function isAuthenticated(): boolean {
  const token = getToken();
  return Boolean(token && token.trim().length > 10);
}

/**
 * Returns an Authorization header dictionary if a token exists.
 */
export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  if (!token) return {};
  return {
    Authorization: `Bearer ${token}`,
  };
}

/**
 * Authenticated fetch wrapper that automatically appends the Bearer token.
 */
export async function authFetch(url: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  const token = getToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(url, {
    ...init,
    headers,
  });
}

/**
 * Registers a new user account against the backend API.
 */
export async function registerUser(payload: AuthRegisterPayload): Promise<UserProfile> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let errorMsg = "Registration failed";
    try {
      const err = await res.json();
      errorMsg = err.error?.message || err.detail || errorMsg;
    } catch {
      // Ignored
    }
    throw new Error(errorMsg);
  }

  return res.json() as Promise<UserProfile>;
}

/**
 * Authenticates user credentials, stores token and profile in localStorage.
 */
export async function loginUser(payload: AuthLoginPayload): Promise<{ token: string; user: UserProfile }> {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let errorMsg = "Authentication failed";
    try {
      const err = await res.json();
      errorMsg = err.error?.message || err.detail || errorMsg;
    } catch {
      // Ignored
    }
    throw new Error(errorMsg);
  }

  const data = (await res.json()) as TokenResponse;
  setToken(data.access_token);

  // Fetch current user details
  const meRes = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    headers: {
      Authorization: `Bearer ${data.access_token}`,
    },
  });

  if (!meRes.ok) {
    throw new Error("Unable to retrieve user profile after login.");
  }

  const user = (await meRes.json()) as UserProfile;
  setStoredUser(user);

  return { token: data.access_token, user };
}

/**
 * Logs out the current user by clearing localStorage and refreshing the window/state.
 */
export function logoutUser(): void {
  clearAuth();
  if (typeof window !== "undefined") {
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.assign("/login");
  }
}


