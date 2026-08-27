"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Cpu, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";
import { useAppStore } from "@/lib/store";

export default function AuthCallbackPage() {
  const router = useRouter();
  const { setUser, setSession } = useAppStore();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function handleAuthCallback() {
      try {
        // 1. Process URL hash or code
        const { data, error } = await supabase.auth.getSession();

        if (error) {
          setStatus("error");
          setErrorMessage(error.message);
          return;
        }

        if (data?.session) {
          setUser(data.session.user);
          setSession(data.session);
          setStatus("success");
          setTimeout(() => {
            router.push("/chat");
          }, 1200);
          return;
        }

        // 2. Listen to onAuthStateChange for token exchange
        const { data: authListener } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            if (event === "SIGNED_IN" || event === "USER_UPDATED" || session) {
              if (session) {
                setUser(session.user);
                setSession(session);
                setStatus("success");
                setTimeout(() => {
                  router.push("/chat");
                }, 1000);
              }
            }
          }
        );

        return () => {
          authListener.subscription.unsubscribe();
        };
      } catch (err) {
        setStatus("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Failed to verify email confirmation."
        );
      }
    }

    handleAuthCallback();
  }, [router, setUser, setSession]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-white px-4 dark:bg-black">
      <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-xl dark:border-gray-800 dark:bg-gray-900">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/25">
          <Cpu className="h-7 w-7 text-white" />
        </div>

        {status === "loading" && (
          <div>
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-indigo-500" />
            <h2 className="mt-4 text-lg font-bold text-gray-900 dark:text-white">
              Confirming your email...
            </h2>
            <p className="mt-1 text-xs text-gray-500">
              Verifying your authentication credentials with Supabase.
            </p>
          </div>
        )}

        {status === "success" && (
          <div>
            <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500" />
            <h2 className="mt-4 text-lg font-bold text-gray-900 dark:text-white">
              Email Verified Successfully!
            </h2>
            <p className="mt-1 text-xs text-gray-500">
              Redirecting you to the Architecture Studio...
            </p>
          </div>
        )}

        {status === "error" && (
          <div>
            <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
            <h2 className="mt-4 text-lg font-bold text-red-600 dark:text-red-400">
              Verification Issue
            </h2>
            <p className="mt-1 text-xs text-gray-500">
              {errorMessage || "Unable to confirm email. You may sign in directly."}
            </p>
            <button
              onClick={() => router.push("/signin")}
              className="mt-6 w-full rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-2.5 text-xs font-semibold text-white shadow-md transition-opacity hover:opacity-90"
            >
              Go to Sign In
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
