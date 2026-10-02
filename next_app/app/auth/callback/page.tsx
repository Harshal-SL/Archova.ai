"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Cpu, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { supabase } from "@/lib/supabaseClient";
import { useAppStore } from "@/lib/store";
import BubbleBg from "@/components/BubbleBg";

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
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-white px-4 text-black dark:bg-black dark:text-white overflow-hidden">
      <BubbleBg opacity="opacity-80 dark:opacity-90" />
      <div className="relative z-10 w-full max-w-md rounded-2xl border border-neutral-300 bg-white/95 p-8 text-center shadow-xl dark:border-neutral-800 dark:bg-black/95 backdrop-blur-xl">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black shadow-md">
          <Cpu className="h-7 w-7" />
        </div>

        {status === "loading" && (
          <div>
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-black dark:text-white" />
            <h2 className="font-heading mt-4 text-lg font-bold tracking-tight text-black dark:text-white">
              Confirming your email...
            </h2>
            <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
              Verifying your authentication credentials with Supabase.
            </p>
          </div>
        )}

        {status === "success" && (
          <div>
            <CheckCircle2 className="mx-auto h-8 w-8 text-black dark:text-white" />
            <h2 className="font-heading mt-4 text-lg font-bold tracking-tight text-black dark:text-white">
              Email Verified Successfully!
            </h2>
            <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
              Redirecting you to the Architecture Studio...
            </p>
          </div>
        )}

        {status === "error" && (
          <div>
            <AlertCircle className="mx-auto h-8 w-8 text-neutral-800 dark:text-neutral-200" />
            <h2 className="font-heading mt-4 text-lg font-bold tracking-tight text-black dark:text-white">
              Verification Issue
            </h2>
            <p className="mt-1 text-xs text-neutral-500 dark:text-neutral-400">
              {errorMessage || "Unable to confirm email. You may sign in directly."}
            </p>
            <button
              onClick={() => router.push("/signin")}
              className="font-heading mt-6 w-full rounded-xl bg-black py-3 text-xs font-semibold text-white shadow-xs transition-all hover:bg-neutral-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200"
            >
              Go to Sign In
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
