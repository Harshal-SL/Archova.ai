export const AUTH_COOKIE_NAME = "archova_session";

/**
 * Synchronizes the Supabase access token with an HTTP-accessible cookie so Next.js middleware
 * and server components can reliably protect routes before page render.
 */
export function syncAuthCookie(token: string | null | undefined) {
  if (typeof document === "undefined") return;

  if (token) {
    const isHttps = typeof window !== "undefined" && window.location.protocol === "https:";
    // Keep session active for 7 days (matching standard JWT lifespan)
    document.cookie = `${AUTH_COOKIE_NAME}=${encodeURIComponent(token)}; path=/; max-age=604800; SameSite=Lax${
      isHttps ? "; Secure" : ""
    }`;
  } else {
    // Clear cookie immediately on logout / invalid session
    document.cookie = `${AUTH_COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax`;
  }
}
