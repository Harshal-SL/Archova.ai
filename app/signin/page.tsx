import AuthCard from "@/components/AuthCard";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In • ArchAI Architecture Studio",
  description: "Sign in to your ArchAI account to access automated system architecture workflows, HLD diagrams, and LLD blueprints.",
};

export default function SignInPage() {
  return <AuthCard initialMode="signin" />;
}
