import AuthCard from "@/components/AuthCard";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Account • ArchAI Architecture Studio",
  description: "Create an account on ArchAI to transform software requirements into high-level and low-level system architecture designs.",
};

export default function SignUpPage() {
  return <AuthCard initialMode="signup" />;
}
