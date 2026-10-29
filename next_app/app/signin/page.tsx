import { Suspense } from "react";
import AuthCard from "@/components/AuthCard";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In • Archova.ai Architecture Studio",
  description: "Sign in to your Archova.ai account to access automated system architecture workflows, HLD diagrams, and LLD blueprints.",
};

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <AuthCard initialMode="signin" />
    </Suspense>
  );
}
