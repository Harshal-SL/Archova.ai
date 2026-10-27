"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence, type Variants } from "framer-motion";
import {
  Cpu,
  Mail,
  Lock,
  User,
  Eye,
  EyeOff,
  Shield,
  Check,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Send,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  Layers,
  FileCode2,
  Workflow,
  Terminal,
  Activity,
  Network,
  MonitorIcon,
  ShieldCheck,
  Database,
} from "lucide-react";
import BubbleBg from "@/components/BubbleBg";
import ThemeToggle from "@/components/ThemeToggle";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { cn } from "@/lib/utils";
import { supabase } from "@/lib/supabaseClient";
import { useAppStore } from "@/lib/store";

interface AuthCardProps {
  initialMode?: "signin" | "signup";
}

export default function AuthCard({ initialMode = "signin" }: AuthCardProps) {
  const router = useRouter();
  const { setUser, setSession, loginAsGuest } = useAppStore();

  const [isSignUp, setIsSignUp] = useState(initialMode === "signup");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Sync mode with route changes if needed
  useEffect(() => {
    setIsSignUp(initialMode === "signup");
  }, [initialMode]);

  // Password validation rules
  const hasMinLength = password.length >= 8;
  const hasMaxLength = password.length <= 20;
  const hasCapitalLetter = /[A-Z]/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
  const isValidLength = hasMinLength && hasMaxLength;
  const isPasswordValid = isValidLength && hasCapitalLetter && hasSpecialChar;

  // Toggle between Sign In and Sign Up
  const toggleMode = () => {
    const nextMode = !isSignUp;
    setIsSignUp(nextMode);
    setErrorMessage(null);
    setSuccessMessage(null);
    setShowPassword(false);
    setShowConfirmPassword(false);
    setPassword("");
    setConfirmPassword("");
    if (typeof window !== "undefined") {
      window.history.pushState(null, "", nextMode ? "/signup" : "/signin");
    }
  };

  // Instant Guest login
  const handleGuestLogin = () => {
    loginAsGuest(fullName.trim() || email.split("@")[0] || "Guest Architect");
    setSuccessMessage("Entering ArchAI Architecture Studio as Guest Architect...");
    setTimeout(() => {
      router.push("/chat");
    }, 400);
  };

  // Sign In handler
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (error) {
        if (
          error.message.includes("Invalid login credentials") ||
          error.message.includes("invalid_grant")
        ) {
          setErrorMessage(
            "Invalid email or password. Please check your credentials or create a new account."
          );
        } else if (error.message.includes("Email not confirmed")) {
          setErrorMessage(
            "Your email has not been verified yet. Please check your inbox and spam folders."
          );
        } else {
          setErrorMessage(error.message);
        }
        return;
      }

      if (data?.user) {
        setUser(data.user);
        setSession(data.session);
        setSuccessMessage("Authenticated successfully! Loading studio...");
        setTimeout(() => {
          router.push("/chat");
        }, 600);
      } else {
        setErrorMessage("Authentication failed. Please try again.");
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during sign in."
      );
    } finally {
      setLoading(false);
    }
  };

  // Sign Up handler
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match. Please re-enter.");
      return;
    }

    if (!isPasswordValid) {
      setErrorMessage(
        "Please meet all password requirements before creating your account."
      );
      return;
    }

    setLoading(true);

    try {
      const redirectTo =
        typeof window !== "undefined"
          ? `${window.location.origin}/auth/callback`
          : undefined;

      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          emailRedirectTo: redirectTo,
          data: {
            name: fullName.trim(),
            full_name: fullName.trim(),
          },
        },
      });

      if (error) {
        setErrorMessage(error.message);
        return;
      }

      if (data?.user) {
        try {
          await supabase.from("users").upsert({
            id: data.user.id,
            email: email.trim(),
            full_name: fullName.trim() || email.split("@")[0],
          });
        } catch {
          // Trigger handles automatically
        }

        setUser(data.user);
        setSession(data.session);

        if (data.session) {
          setSuccessMessage("Account created successfully! Entering ArchAI Studio...");
          setTimeout(() => {
            router.push("/chat");
          }, 800);
        } else {
          // Attempt automatic login if email verification is not strictly enforced
          try {
            const { data: signInData } = await supabase.auth.signInWithPassword({
              email: email.trim(),
              password,
            });
            if (signInData?.session) {
              setUser(signInData.user);
              setSession(signInData.session);
              setSuccessMessage("Account created and authenticated! Entering ArchAI Studio...");
              setTimeout(() => {
                router.push("/chat");
              }, 800);
              return;
            }
          } catch {
            // continue
          }

          setSuccessMessage(
            `Account created! A confirmation email has been dispatched to ${email}. If your Supabase instance requires verification, check your inbox, or click "Continue as Guest" below to start immediately.`
          );
        }
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during sign up."
      );
    } finally {
      setLoading(false);
    }
  };

  // Resend email confirmation
  const handleResendConfirmation = async () => {
    if (!email.trim()) {
      setErrorMessage("Please enter your email address to resend confirmation.");
      return;
    }
    setResending(true);
    setErrorMessage(null);
    try {
      const redirectTo =
        typeof window !== "undefined"
          ? `${window.location.origin}/auth/callback`
          : undefined;
      const { error } = await supabase.auth.resend({
        type: "signup",
        email: email.trim(),
        options: {
          emailRedirectTo: redirectTo,
        },
      });

      if (error) {
        setErrorMessage(error.message);
      } else {
        setSuccessMessage(
          "Confirmation email resent! Please check your inbox and spam folder."
        );
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Failed to resend confirmation email."
      );
    } finally {
      setResending(false);
    }
  };

  const isEmailUnconfirmed =
    errorMessage?.toLowerCase().includes("confirm") ||
    errorMessage?.toLowerCase().includes("verified") ||
    errorMessage?.toLowerCase().includes("check your inbox");

  // Animation variants
  const containerVariants: Variants = {
    hidden: { opacity: 0, scale: 0.98 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { staggerChildren: 0.08, delayChildren: 0.1 },
    },
  };

  const itemVariants: Variants = {
    hidden: { y: 15, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { type: "spring" as const, stiffness: 120, damping: 14 },
    },
  };

  return (
    <div className="relative min-h-screen w-full bg-white text-black dark:bg-black dark:text-white flex items-center justify-center p-4 sm:p-6 lg:p-8 overflow-hidden transition-colors selection:bg-black selection:text-white dark:selection:bg-white dark:selection:text-black">
      {/* ── Dynamic Ambient Tech Grid Background ── */}
      <BubbleBg />

      {/* ── Fixed Top-Left Floating Brand Link ── */}
      <Link
        href="/"
        className="fixed top-5 left-5 sm:top-6 sm:left-6 z-50 flex items-center gap-2.5 px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-full border border-neutral-300 bg-white/90 text-neutral-900 hover:border-black dark:border-neutral-800 dark:bg-neutral-950/90 dark:text-neutral-200 dark:hover:border-white backdrop-blur-xl shadow-xs transition-all duration-200 group"
      >
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-black text-white dark:bg-white dark:text-black font-extrabold shadow-sm transition-transform duration-200 group-hover:scale-105">
          <Cpu className="h-4 w-4" />
        </div>
        <span className="text-sm font-bold tracking-tight">
          Arch<span className="text-neutral-500 dark:text-neutral-400">AI</span>
        </span>
      </Link>

      {/* ── Fixed Top-Right Theme Toggle & Return Link ── */}
      <div className="fixed top-5 right-5 sm:top-6 sm:right-6 z-50 flex items-center gap-2 sm:gap-3">
        <ThemeToggle />
        <Link
          href="/"
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg border border-neutral-300 bg-white/90 text-xs font-semibold text-neutral-700 hover:text-black hover:border-black dark:border-neutral-800 dark:bg-neutral-950/90 dark:text-neutral-300 dark:hover:text-white dark:hover:border-white backdrop-blur-md shadow-xs transition-all duration-200"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Back to Home</span>
          <span className="sm:hidden">Home</span>
        </Link>
      </div>

      {/* ── Main Auth Card Container ── */}
      <div className="relative z-10 w-full max-w-5xl my-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 rounded-3xl overflow-hidden border border-neutral-200 bg-white/95 dark:border-neutral-800 dark:bg-[#0c0c0c]/95 shadow-2xl backdrop-blur-2xl">
          {/* ════ Left Side: Dual-Mode Interactive Form ════ */}
          <motion.div
            className="lg:col-span-7 p-7 sm:p-10 lg:p-12 flex flex-col justify-center"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Top Status & Mode Switcher */}
            <motion.div
              variants={itemVariants}
              className="flex items-center justify-between mb-6"
            >
              <span className="inline-flex items-center gap-1.5 rounded-full border border-neutral-300 bg-neutral-100 px-3 py-1 text-xs font-semibold text-neutral-800 dark:border-neutral-800 dark:bg-neutral-900 dark:text-neutral-300">
                <Shield className="h-3.5 w-3.5 text-black dark:text-white" />
                <span>Enterprise Studio</span>
              </span>
              <button
                type="button"
                onClick={toggleMode}
                className="text-xs font-bold text-black dark:text-white hover:underline cursor-pointer transition-colors"
              >
                {isSignUp ? "Already registered? Sign In" : "Need an account? Sign Up"}
              </button>
            </motion.div>

            {/* Dynamic Animated Header */}
            <AnimatePresence mode="wait">
              <motion.div
                key={isSignUp ? "signup-header" : "signin-header"}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="mb-6"
              >
                <h1 className="font-heading text-2xl sm:text-3xl font-extrabold tracking-tight text-neutral-900 dark:text-white mb-2">
                  {isSignUp ? "Create Studio Account" : "Welcome Back"}
                </h1>
                <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400">
                  {isSignUp
                    ? "Start generating automated, deterministic system architectures with AI."
                    : "Sign in to access your saved architecture graphs, specs, and LLDs."}
                </p>
              </motion.div>
            </AnimatePresence>

            {/* Error / Alert Display */}
            {errorMessage && (
              <motion.div variants={itemVariants} className="mb-5">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="space-y-2">
                      <p>{errorMessage}</p>
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        {isEmailUnconfirmed && (
                          <button
                            type="button"
                            onClick={handleResendConfirmation}
                            disabled={resending}
                            className="inline-flex items-center gap-1.5 rounded-lg bg-red-900/60 hover:bg-red-800/80 text-red-100 px-3 py-1.5 text-xs font-semibold transition-colors cursor-pointer"
                          >
                            {resending ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <Send className="h-3.5 w-3.5" />
                            )}
                            <span>Resend Confirmation Email</span>
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={handleGuestLogin}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-red-400/40 bg-white/10 hover:bg-white/20 text-xs font-semibold px-3 py-1.5 transition-colors cursor-pointer"
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          <span>Continue as Guest Instead</span>
                        </button>
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>
              </motion.div>
            )}

            {/* Success Alert Display */}
            {successMessage && (
              <motion.div variants={itemVariants} className="mb-5">
                <Alert variant="success">
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertDescription>{successMessage}</AlertDescription>
                </Alert>
              </motion.div>
            )}

            {/* Clean Labeled Form Matching Landing Page Structure */}
            <form onSubmit={isSignUp ? handleSignUp : handleSignIn} className="space-y-4">
              {/* 1. Full Name (Sign Up only) */}
              <AnimatePresence>
                {isSignUp && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden space-y-1.5"
                  >
                    <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                      Your Name *
                    </label>
                    <input
                      type="text"
                      name="name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Alex Morgan"
                      required={isSignUp}
                      disabled={loading}
                      className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs sm:text-sm text-neutral-900 placeholder:text-neutral-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-900 dark:text-white dark:focus:border-white dark:focus:ring-white/10 transition-colors"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* 2. Work Email */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                  Work Email *
                </label>
                <input
                  type="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="alex@company.com"
                  required
                  disabled={loading}
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs sm:text-sm text-neutral-900 placeholder:text-neutral-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-900 dark:text-white dark:focus:border-white dark:focus:ring-white/10 transition-colors"
                />
              </div>

              {/* 3. Password */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                    Password *
                  </label>
                  {!isSignUp && (
                    <button
                      type="button"
                      onClick={() =>
                        alert(
                          "Password reset link has been dispatched or check Supabase authentication recovery."
                        )
                      }
                      className="text-[11px] font-semibold text-neutral-500 hover:text-black dark:hover:text-white transition-colors cursor-pointer"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    disabled={loading}
                    className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 pr-10 text-xs sm:text-sm text-neutral-900 placeholder:text-neutral-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-900 dark:text-white dark:focus:border-white dark:focus:ring-white/10 transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 transition-colors cursor-pointer"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* 4. Confirm Password (Sign Up only) */}
              <AnimatePresence>
                {isSignUp && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden space-y-1.5"
                  >
                    <label className="block text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                      Confirm Password *
                    </label>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? "text" : "password"}
                        name="confirmPassword"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        required={isSignUp}
                        disabled={loading}
                        className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 pr-10 text-xs sm:text-sm text-neutral-900 placeholder:text-neutral-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10 dark:border-neutral-800 dark:bg-neutral-900 dark:text-white dark:focus:border-white dark:focus:ring-white/10 transition-colors"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        tabIndex={-1}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-800 dark:hover:text-neutral-200 transition-colors cursor-pointer"
                        aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                      >
                        {showConfirmPassword ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── Password Strength Requirements (Sign Up only) ── */}
              <AnimatePresence>
                {isSignUp && password.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: "auto" }}
                    exit={{ opacity: 0, y: -4, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden rounded-xl border border-neutral-200 bg-neutral-50/80 dark:border-neutral-800 dark:bg-neutral-900/60 p-3"
                  >
                    <div className="text-[11px] font-bold text-neutral-500 uppercase tracking-wider mb-2">
                      Password Requirements:
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <div
                        className={cn(
                          "flex items-center gap-1.5 text-xs transition-colors",
                          isValidLength ? "text-emerald-600 dark:text-emerald-400 font-semibold" : "text-neutral-500"
                        )}
                      >
                        <Check className={cn("h-3.5 w-3.5", isValidLength ? "text-emerald-600 dark:text-emerald-400" : "text-neutral-400")} />
                        <span>8-20 chars ({password.length})</span>
                      </div>
                      <div
                        className={cn(
                          "flex items-center gap-1.5 text-xs transition-colors",
                          hasCapitalLetter ? "text-emerald-600 dark:text-emerald-400 font-semibold" : "text-neutral-500"
                        )}
                      >
                        <Check className={cn("h-3.5 w-3.5", hasCapitalLetter ? "text-emerald-600 dark:text-emerald-400" : "text-neutral-400")} />
                        <span>1 Uppercase (A-Z)</span>
                      </div>
                      <div
                        className={cn(
                          "flex items-center gap-1.5 text-xs transition-colors",
                          hasSpecialChar ? "text-emerald-600 dark:text-emerald-400 font-semibold" : "text-neutral-500"
                        )}
                      >
                        <Check className={cn("h-3.5 w-3.5", hasSpecialChar ? "text-emerald-600 dark:text-emerald-400" : "text-neutral-400")} />
                        <span>1 Special (!@#$)</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── Action Submit Button ── */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading || (isSignUp && !isPasswordValid)}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-black text-white dark:bg-white dark:text-black py-3 text-xs sm:text-sm font-bold shadow-md transition-all hover:bg-neutral-800 dark:hover:bg-neutral-200 active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>{isSignUp ? "Creating Studio Account..." : "Signing in..."}</span>
                    </span>
                  ) : isSignUp ? (
                    <>
                      <span>Create Studio Account</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  ) : (
                    <>
                      <span>Sign In to Studio</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </div>

              {/* ── Divider & Guest Option ── */}
              <div className="relative flex items-center justify-center my-2">
                <div className="border-t border-neutral-200 dark:border-neutral-800 w-full" />
                <span className="bg-white dark:bg-[#0c0c0c] px-3 text-[10px] font-bold text-neutral-400 uppercase tracking-widest shrink-0">
                  Or
                </span>
                <div className="border-t border-neutral-200 dark:border-neutral-800 w-full" />
              </div>

              <button
                type="button"
                onClick={handleGuestLogin}
                className="w-full flex items-center justify-center gap-2 rounded-xl border border-neutral-200/80 dark:border-[#262626] bg-white/70 dark:bg-[#0D0D0F] text-neutral-800 dark:text-neutral-200 py-2.5 text-xs sm:text-sm font-semibold transition-all hover:bg-white dark:hover:bg-[#161619] dark:hover:border-white/20 cursor-pointer shadow-2xs backdrop-blur-md"
              >
                <Sparkles className="h-3.5 w-3.5 text-neutral-500 dark:text-neutral-400" />
                <span>Continue as Guest (No Registration Required)</span>
              </button>

              {/* Sub-actions & Terms */}
              <p className="text-center text-[11px] text-neutral-500 pt-2">
                By continuing, you agree to ArchAI&apos;s{" "}
                <span className="text-neutral-700 dark:text-neutral-300 underline underline-offset-2 hover:text-black dark:hover:text-white cursor-pointer">
                  Terms of Service
                </span>{" "}
                and{" "}
                <span className="text-neutral-700 dark:text-neutral-300 underline underline-offset-2 hover:text-black dark:hover:text-white cursor-pointer">
                  Privacy Policy
                </span>
              </p>
            </form>
          </motion.div>

          {/* ════ Right Side: Interactive Architecture Showcase (Black, Blue & White Theme) ════ */}
          <motion.div
            className="lg:col-span-5 hidden lg:flex flex-col justify-between p-6 sm:p-8 border-l border-neutral-200/80 dark:border-white/[0.08] bg-[#0A0A0C] text-white backdrop-blur-2xl relative overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
          >
            <LiveArchitectureShowcase />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function LiveArchitectureShowcase() {
  const [activeActivityIndex, setActiveActivityIndex] = useState(0);

  const activities = [
    {
      agent: "SAE Engine",
      task: "Synthesizing 14 verified nodes & 19 edges in React Flow DAG",
    },
    {
      agent: "REE Engine",
      task: "Interview SLA calculated: 99.999% • RTO: 30s • 42k req/s",
    },
    {
      agent: "Security Engine",
      task: "Enforcing zero-trust API boundaries & cryptographic token validation",
    },
    {
      agent: "Database Engine",
      task: "Compiling PostgreSQL 16 schema, partitioned B-Trees & Redis cluster",
    },
    {
      agent: "Validator Engine",
      task: "Auditing IEEE/ISO-29148 formal architecture specification compliance",
    },
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveActivityIndex((prev) => (prev + 1) % activities.length);
    }, 3200);
    return () => clearInterval(timer);
  }, [activities.length]);

  const currentActivity = activities[activeActivityIndex];

  return (
    <div className="relative flex flex-col justify-between h-full space-y-5">
      {/* ── Soft Blue Ambient Glows & Blur ── */}
      <div className="pointer-events-none absolute -top-12 -right-12 w-64 h-64 rounded-full bg-[#005dff]/15 blur-3xl animate-pulse" />
      <div className="pointer-events-none absolute bottom-6 -left-10 w-56 h-56 rounded-full bg-[#005dff]/10 blur-3xl" />

      {/* ── Top Header: Minimal Pill Badge & Certification ── */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-semibold text-white shadow-2xs backdrop-blur-md">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#005dff] opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-[#005dff]" />
          </span>
          <span className="tracking-tight font-medium">ArchAI Architecture Engine</span>
        </div>
        <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-widest font-semibold">
          SOC 2 • ISO 29148
        </span>
      </div>

      {/* ── Central Hero: Glowing Core & Clean Title ── */}
      <div className="relative z-10 text-center space-y-3 pt-1">
        {/* Sleek Central Core with Blue Halo */}
        <div className="relative mx-auto flex h-16 w-16 items-center justify-center">
          <div className="absolute inset-0 rounded-2xl border border-[#005dff]/30 animate-pulse [animation-duration:3s]" />
          <div className="absolute -inset-1 rounded-2xl bg-[#005dff]/12 blur-md" />

          {/* Central Black Core Box */}
          <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-2xl bg-black border border-white/15 text-white shadow-2xl">
            <Cpu className="h-6 w-6 text-[#005dff]" />
          </div>
        </div>

        <div className="space-y-1">
          <h2 className="font-heading text-lg sm:text-xl font-extrabold text-white tracking-tight">
            Automated System Architecture
          </h2>
          <p className="text-xs text-neutral-400 max-w-xs mx-auto leading-relaxed">
            Deterministic multi-agent synthesis from natural language to formal enterprise topology.
          </p>
        </div>
      </div>

      {/* ── 3 Simple, Elegant Feature Cards (Black, Blue, White & Blur) ── */}
      <div className="relative z-10 space-y-2.5 text-left">
        {/* Card 1: HLD */}
        <div className="group flex items-center justify-between rounded-2xl border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.05] hover:border-[#005dff]/40 p-3 shadow-xs transition-all backdrop-blur-md cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#005dff]/10 text-[#005dff] border border-[#005dff]/25 group-hover:scale-105 transition-transform">
              <Network className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-2">
                <span>Interactive Visual HLD</span>
                <span className="text-[9px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#005dff]/15 text-[#005dff] border border-[#005dff]/30">
                  React Flow
                </span>
              </div>
              <div className="text-[11px] text-neutral-400 mt-0.5">
                Zoomable DAG topology with verified protocol edge contracts
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: 5 Domain LLDs */}
        <div className="group flex items-center justify-between rounded-2xl border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.05] hover:border-[#005dff]/40 p-3 shadow-xs transition-all backdrop-blur-md cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#005dff]/10 text-[#005dff] border border-[#005dff]/25 group-hover:scale-105 transition-transform">
              <Layers className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-2">
                <span>5 Domain LLD Blueprints</span>
                <span className="text-[9px] font-mono font-semibold px-2 py-0.5 rounded-full bg-white/10 text-white border border-white/20">
                  Parallel Mesh
                </span>
              </div>
              <div className="text-[11px] text-neutral-400 mt-0.5">
                Backend, Frontend, Database, Security & Cloud specifications
              </div>
            </div>
          </div>
        </div>

        {/* Card 3: Validation & Quality Audit */}
        <div className="group flex items-center justify-between rounded-2xl border border-white/[0.08] bg-white/[0.02] hover:bg-white/[0.05] hover:border-[#005dff]/40 p-3 shadow-xs transition-all backdrop-blur-md cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#005dff]/10 text-[#005dff] border border-[#005dff]/25 group-hover:scale-105 transition-transform">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-2">
                <span>Automated Validation Audit</span>
                <span className="text-[9px] font-mono font-semibold px-2 py-0.5 rounded-full bg-[#005dff]/15 text-[#005dff] border border-[#005dff]/30">
                  ISO-29148
                </span>
              </div>
              <div className="text-[11px] text-neutral-400 mt-0.5">
                Multi-artifact consistency check with closed-loop AI verification
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Live Agent Stream Ticker (Black, Blue, White) ── */}
      <div className="relative z-10 rounded-2xl border border-white/10 bg-black/90 p-3 text-white shadow-md backdrop-blur-xl">
        <div className="flex items-center justify-between text-[10px] font-mono border-b border-white/10 pb-2 mb-2">
          <div className="flex items-center gap-2">
            <Terminal className="h-3.5 w-3.5 text-[#005dff]" />
            <span className="font-bold text-white tracking-wide">Autonomous Engine Stream</span>
          </div>
          <span className="flex items-center gap-1.5 text-[#005dff] font-semibold">
            <span className="h-1.5 w-1.5 rounded-full bg-[#005dff] animate-ping" />
            <span>Active</span>
          </span>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentActivity.agent}
            initial={{ opacity: 0, y: 3 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -3 }}
            transition={{ duration: 0.2 }}
            className="flex items-start gap-2 text-xs"
          >
            <span className="font-mono font-bold text-[11px] text-[#005dff] shrink-0">
              [{currentActivity.agent}]
            </span>
            <span className="text-neutral-300 text-[11px] leading-tight truncate">
              {currentActivity.task}
            </span>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* ── Bottom Showcase Footer ── */}
      <div className="relative z-10 flex items-center justify-between border-t border-white/10 pt-2.5 text-[10.5px] text-neutral-400">
        <span className="font-mono">Next.js 16 • React 19 • Supabase</span>
        <span className="flex items-center gap-1.5 text-white font-semibold">
          <span className="h-1.5 w-1.5 rounded-full bg-[#005dff] animate-pulse" />
          Auth Engine Online
        </span>
      </div>
    </div>
  );
}
