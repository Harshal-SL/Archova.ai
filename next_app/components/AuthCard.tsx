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
  Sparkles,
  Layers,
  FileCode2,
  Workflow,
} from "lucide-react";
import { Particles } from "@/components/ui/Particles";
import { Button } from "@/components/ui/Button";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { cn } from "@/lib/utils";
import { supabase } from "@/lib/supabaseClient";
import { useAppStore } from "@/lib/store";

interface AuthCardProps {
  initialMode?: "signin" | "signup";
}

export default function AuthCard({ initialMode = "signin" }: AuthCardProps) {
  const router = useRouter();
  const { setUser, setSession } = useAppStore();

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
    // Update browser URL without reloading page
    if (typeof window !== "undefined") {
      window.history.pushState(null, "", nextMode ? "/signup" : "/signin");
    }
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

    // Validate confirmation
    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match. Please re-enter.");
      return;
    }

    // Validate strength
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
        // Upsert into users table if table trigger isn't configured
        try {
          await supabase.from("users").upsert({
            id: data.user.id,
            email: email.trim(),
            name: fullName.trim() || email.split("@")[0],
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
          setSuccessMessage(
            `Account created! A confirmation email has been sent to ${email}. Please check your inbox & spam folder.`
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
    <div className="relative min-h-screen w-full bg-black text-white flex items-center justify-center p-4 sm:p-6 lg:p-8 overflow-hidden select-none">
      {/* ── Interactive Canvas Particles Background ── */}
      <Particles
        className="absolute inset-0 z-0"
        quantity={150}
        ease={75}
        color="#60a5fa"
        size={0.45}
        refresh={false}
      />

      {/* Ambient background glow accents */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-gradient-to-b from-blue-600/15 via-purple-600/10 to-transparent blur-[120px] rounded-full" />
      <div className="pointer-events-none absolute -bottom-40 right-10 w-[500px] h-[400px] bg-blue-500/10 blur-[140px] rounded-full" />

      {/* ── Fixed Top-Left Floating Pill Badge ── */}
      <Link
        href="/"
        className="fixed top-6 left-6 z-50 flex items-center gap-2.5 px-4 py-2 rounded-full bg-neutral-950/70 hover:bg-neutral-900 border border-neutral-800 text-neutral-200 hover:text-white backdrop-blur-xl shadow-lg transition-all duration-200 group"
      >
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white text-black font-extrabold shadow-sm transition-transform duration-200 group-hover:scale-105">
          <Cpu className="h-4 w-4" />
        </div>
        <span className="text-sm font-bold tracking-tight">ArchAI</span>
      </Link>

      {/* ── Fixed Top-Right Return Link ── */}
      <Link
        href="/"
        className="fixed top-6 right-6 z-50 hidden sm:flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-neutral-950/50 hover:bg-neutral-900/80 border border-neutral-800/80 text-xs font-semibold text-neutral-400 hover:text-neutral-200 backdrop-blur-md transition-all duration-200"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        <span>Back to Home</span>
      </Link>

      {/* ── Main Auth Card Container ── */}
      <div className="relative z-10 w-full max-w-5xl my-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 rounded-3xl overflow-hidden bg-neutral-950/85 border border-neutral-800/90 shadow-[0_0_80px_rgba(0,0,0,0.85)] backdrop-blur-2xl">
          {/* ════ Left Side: Dual-Mode Interactive Form ════ */}
          <motion.div
            className="p-8 sm:p-12 flex flex-col justify-center"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* Top Status & Mode Switcher */}
            <motion.div
              variants={itemVariants}
              className="flex items-center justify-between mb-6"
            >
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-neutral-400">
                <Shield className="h-3.5 w-3.5 text-blue-400" />
                <span>Secure Architecture Studio</span>
              </span>
              <button
                type="button"
                onClick={toggleMode}
                className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors cursor-pointer"
              >
                {isSignUp ? "Already have an account?" : "Need an account?"}
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
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-2">
                  {isSignUp ? "Create Account" : "Welcome Back"}
                </h1>
                <p className="text-sm text-neutral-400">
                  {isSignUp
                    ? "Start designing automated system architectures with AI"
                    : "Sign in to access your ArchAI Architecture Studio"}
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
                      {isEmailUnconfirmed && (
                        <button
                          type="button"
                          onClick={handleResendConfirmation}
                          disabled={resending}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-red-900/60 hover:bg-red-800/80 text-red-100 px-3 py-1.5 text-xs font-semibold transition-colors"
                        >
                          {resending ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Send className="h-3.5 w-3.5" />
                          )}
                          <span>Resend Confirmation Email</span>
                        </button>
                      )}
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

            {/* The Form */}
            <form onSubmit={isSignUp ? handleSignUp : handleSignIn} className="space-y-5">
              {/* ── Connected Input Container with Vertical Dashed Guide Line ── */}
              <motion.div
                variants={itemVariants}
                className="relative rounded-2xl bg-neutral-900/50 border border-neutral-800/90 p-4 sm:p-5 backdrop-blur-md"
              >
                {/* Vertical Dashed Guide Line connecting the badges */}
                <div
                  className="absolute left-[30px] sm:left-[34px] top-9 bottom-9 w-px border-l border-dashed border-neutral-700/80 pointer-events-none"
                  aria-hidden="true"
                />

                {/* 1. Full Name (Sign Up only) */}
                <AnimatePresence>
                  {isSignUp && (
                    <motion.div
                      initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                      animate={{ opacity: 1, height: "auto", marginBottom: 12 }}
                      exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden"
                    >
                      <div className="relative flex items-center">
                        <div className="z-10 flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full bg-neutral-950 border border-neutral-700 text-neutral-300 shadow-sm">
                          <User className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                        </div>
                        <input
                          type="text"
                          name="name"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          placeholder="Full Name (e.g. Alex Morgan)"
                          required={isSignUp}
                          disabled={loading}
                          className="w-full bg-transparent pl-3.5 pr-3 py-2 text-sm text-white placeholder:text-neutral-500 focus:outline-none"
                        />
                      </div>
                      <hr className="border-neutral-800/70 ml-10 sm:ml-12 mt-2" />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* 2. Work Email */}
                <div className="relative flex items-center mb-2">
                  <div className="z-10 flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full bg-neutral-950 border border-neutral-700 text-neutral-300 shadow-sm">
                    <Mail className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  </div>
                  <input
                    type="email"
                    name="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Work Email (engineer@company.com)"
                    required
                    disabled={loading}
                    className="w-full bg-transparent pl-3.5 pr-3 py-2 text-sm text-white placeholder:text-neutral-500 focus:outline-none"
                  />
                </div>

                <hr className="border-neutral-800/70 ml-10 sm:ml-12" />

                {/* 3. Password */}
                <div className="relative flex items-center mt-2 mb-2">
                  <div className="z-10 flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full bg-neutral-950 border border-neutral-700 text-neutral-300 shadow-sm">
                    <Lock className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Password"
                    required
                    disabled={loading}
                    className="w-full bg-transparent pl-3.5 pr-10 py-2 text-sm text-white placeholder:text-neutral-500 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                    className="absolute right-2 p-1.5 text-neutral-400 hover:text-white transition-colors cursor-pointer"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <Eye className="h-4 w-4" />
                    ) : (
                      <EyeOff className="h-4 w-4" />
                    )}
                  </button>
                </div>

                {/* 4. Confirm Password (Sign Up only) */}
                <AnimatePresence>
                  {isSignUp && (
                    <motion.div
                      initial={{ opacity: 0, height: 0, marginTop: 0 }}
                      animate={{ opacity: 1, height: "auto", marginTop: 2 }}
                      exit={{ opacity: 0, height: 0, marginTop: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden"
                    >
                      <hr className="border-neutral-800/70 ml-10 sm:ml-12 mb-2" />
                      <div className="relative flex items-center">
                        <div className="z-10 flex h-7 w-7 sm:h-8 sm:w-8 shrink-0 items-center justify-center rounded-full bg-neutral-950 border border-neutral-700 text-neutral-300 shadow-sm">
                          <Lock className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                        </div>
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          name="confirmPassword"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="Confirm Password"
                          required={isSignUp}
                          disabled={loading}
                          className="w-full bg-transparent pl-3.5 pr-10 py-2 text-sm text-white placeholder:text-neutral-500 focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={() =>
                            setShowConfirmPassword(!showConfirmPassword)
                          }
                          tabIndex={-1}
                          className="absolute right-2 p-1.5 text-neutral-400 hover:text-white transition-colors cursor-pointer"
                          aria-label={
                            showConfirmPassword
                              ? "Hide confirm password"
                              : "Show confirm password"
                          }
                        >
                          {showConfirmPassword ? (
                            <Eye className="h-4 w-4" />
                          ) : (
                            <EyeOff className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>

              {/* ── Interactive Password Strength Rules (Live check indicators) ── */}
              <AnimatePresence>
                {isSignUp && password.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -6, height: 0 }}
                    animate={{ opacity: 1, y: 0, height: "auto" }}
                    exit={{ opacity: 0, y: -6, height: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden rounded-xl bg-neutral-900/40 border border-neutral-800/80 p-3.5"
                  >
                    <div className="text-xs font-semibold text-neutral-400 mb-2">
                      Password Requirements:
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {/* Rule 1: Length */}
                      <div
                        className={cn(
                          "flex items-center gap-1.5 text-xs transition-colors duration-200",
                          isValidLength
                            ? "text-emerald-400 font-medium"
                            : "text-neutral-500"
                        )}
                      >
                        <div
                          className={cn(
                            "flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-colors",
                            isValidLength
                              ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-400"
                              : "border-neutral-700 bg-neutral-800 text-neutral-600"
                          )}
                        >
                          <Check className="h-2.5 w-2.5" />
                        </div>
                        <span>
                          8-20 chars{" "}
                          <span className="opacity-75">
                            ({password.length})
                          </span>
                        </span>
                      </div>

                      {/* Rule 2: Uppercase */}
                      <div
                        className={cn(
                          "flex items-center gap-1.5 text-xs transition-colors duration-200",
                          hasCapitalLetter
                            ? "text-emerald-400 font-medium"
                            : "text-neutral-500"
                        )}
                      >
                        <div
                          className={cn(
                            "flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-colors",
                            hasCapitalLetter
                              ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-400"
                              : "border-neutral-700 bg-neutral-800 text-neutral-600"
                          )}
                        >
                          <Check className="h-2.5 w-2.5" />
                        </div>
                        <span>1 Uppercase (A-Z)</span>
                      </div>

                      {/* Rule 3: Special Character */}
                      <div
                        className={cn(
                          "flex items-center gap-1.5 text-xs transition-colors duration-200",
                          hasSpecialChar
                            ? "text-emerald-400 font-medium"
                            : "text-neutral-500"
                        )}
                      >
                        <div
                          className={cn(
                            "flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-colors",
                            hasSpecialChar
                              ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-400"
                              : "border-neutral-700 bg-neutral-800 text-neutral-600"
                          )}
                        >
                          <Check className="h-2.5 w-2.5" />
                        </div>
                        <span>1 Special (!@#$)</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── Neon-Border Glowing Action Button ── */}
              <motion.div variants={itemVariants} className="space-y-4 pt-2">
                <Button
                  type="submit"
                  variant="glow"
                  size="lg"
                  neon={true}
                  disabled={loading || (isSignUp && !isPasswordValid)}
                  className="w-full py-3.5 text-sm font-bold tracking-wide uppercase shadow-lg cursor-pointer"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>{isSignUp ? "Creating Studio..." : "Authenticating..."}</span>
                    </span>
                  ) : isSignUp ? (
                    "Create Studio Account"
                  ) : (
                    "Sign In to Studio"
                  )}
                </Button>

                {/* Sub-actions */}
                <div className="flex flex-col items-center gap-3 pt-1 text-xs text-neutral-500">
                  {!isSignUp && (
                    <button
                      type="button"
                      onClick={() =>
                        alert(
                          "Password reset link has been dispatched to administrators or use Supabase recovery."
                        )
                      }
                      className="text-neutral-400 hover:text-white transition-colors cursor-pointer"
                    >
                      Forgot your password?
                    </button>
                  )}

                  <p className="text-center text-[11px] text-neutral-500">
                    By continuing, you agree to ArchAI&apos;s{" "}
                    <span className="text-neutral-400 underline underline-offset-2 hover:text-white cursor-pointer">
                      Terms of Service
                    </span>{" "}
                    and{" "}
                    <span className="text-neutral-400 underline underline-offset-2 hover:text-white cursor-pointer">
                      Privacy Policy
                    </span>
                  </p>
                </div>
              </motion.div>
            </form>
          </motion.div>

          {/* ════ Right Side: Modern Hero Showcase Panel ════ */}
          <motion.div
            className="hidden lg:flex flex-col justify-between p-10 xl:p-12 relative overflow-hidden bg-gradient-to-br from-neutral-900 via-neutral-950 to-black border-l border-neutral-800/80"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            {/* Ambient gradients */}
            <div className="absolute top-0 right-0 w-80 h-80 bg-blue-500/10 blur-[90px] rounded-full pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-80 h-80 bg-purple-500/10 blur-[90px] rounded-full pointer-events-none" />

            {/* Top Showcase Meta Badge */}
            <div className="relative z-10 flex items-center justify-between">
              <span className="inline-flex items-center gap-2 rounded-full border border-neutral-700/80 bg-neutral-900/80 px-3.5 py-1 text-xs font-semibold text-neutral-300 backdrop-blur-md">
                <Sparkles className="h-3 w-3 text-blue-400" />
                <span>ArchAI Multi-Agent v2.4</span>
              </span>
              <span className="text-[11px] font-mono text-neutral-500 uppercase tracking-widest">
                Production-Ready
              </span>
            </div>

            {/* Center Graphic & Mission Statement */}
            <div className="relative z-10 my-auto py-8 text-center space-y-6">
              {/* Glowing Icon Frame */}
              <div className="relative mx-auto flex h-24 w-24 items-center justify-center rounded-3xl bg-neutral-900 border border-neutral-700/90 shadow-[0_0_50px_rgba(59,130,246,0.25)]">
                <Cpu className="h-12 w-12 text-blue-400 animate-pulse" />
                <div className="absolute inset-0 rounded-3xl border border-blue-500/30 animate-ping opacity-25 pointer-events-none" />
              </div>

              <div className="space-y-2">
                <h2 className="text-2xl xl:text-3xl font-extrabold text-white tracking-tight">
                  Automated System Architecture
                </h2>
                <p className="text-sm text-neutral-400 max-w-sm mx-auto leading-relaxed">
                  Transform simple requirements into interactive HLD diagrams,
                  multi-service LLD blueprints, and comprehensive ARSRS documentation.
                </p>
              </div>

              {/* Feature Highlights Grid */}
              <div className="grid grid-cols-1 gap-2.5 text-left max-w-sm mx-auto pt-2">
                <div className="flex items-center gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-2.5 backdrop-blur-sm">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    <Workflow className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-neutral-200">
                      High-Level Design (HLD)
                    </div>
                    <div className="text-[10px] text-neutral-400">
                      Interactive React Flow graphs & cloud topology
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-2.5 backdrop-blur-sm">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Layers className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-neutral-200">
                      5 Low-Level Designs (LLDs)
                    </div>
                    <div className="text-[10px] text-neutral-400">
                      Backend, Frontend, Database, Security & Cloud
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 rounded-xl border border-neutral-800 bg-neutral-900/60 p-2.5 backdrop-blur-sm">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <FileCode2 className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-neutral-200">
                      ARSRS Specification Generator
                    </div>
                    <div className="text-[10px] text-neutral-400">
                      IEEE-compliant architectural documentation
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Showcase Footer */}
            <div className="relative z-10 flex items-center justify-between border-t border-neutral-800/80 pt-4 text-[11px] text-neutral-500">
              <span>Next.js 16 • React 19 • Supabase</span>
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Auth Online
              </span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
