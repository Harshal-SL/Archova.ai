import { Suspense } from "react";
import AuthCard from "@/components/AuthCard";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Account • Archova.ai Architecture Studio",
  description: "Create an account on Archova.ai to transform software requirements into high-level and low-level system architecture designs.",
};

export default function SignUpPage() {
  return (
    <Suspense fallback={null}>
      <AuthCard initialMode="signup" />
    </Suspense>
  );
}
