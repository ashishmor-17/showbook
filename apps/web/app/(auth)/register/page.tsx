"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "../../../store/useAuthStore";
import { authApi } from "../../../lib/api";
import { Lock, Mail, User, Film, AlertCircle, Sparkles, CheckCircle2 } from "lucide-react";
import { Skeleton } from "../../../components/ui/Skeleton";

function RegisterContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get("redirect") || "/";

  const { hydrate } = useAuthStore();
  const [step, setStep] = useState(1); // 1 = Registration form, 2 = OTP verification
  
  // Registration form inputs
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // OTP input
  const [otp, setOtp] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      await authApi.register({ name, email, password });
      setStep(2); // Go to OTP step
      setSuccessMsg("Registration successful! Please enter the verification code.");
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.error?.message || "Failed to register account.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.verifyOtp({ email, otp });
      setSuccessMsg("Email verified successfully! redirecting to login...");
      setTimeout(() => {
        router.push(`/login?redirect=${encodeURIComponent(redirectUrl)}`);
      }, 1500);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.error?.message || "Invalid OTP code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-10 flex flex-col gap-6 w-full text-left my-auto">
      {/* Brand Header */}
      <div className="flex flex-col items-center text-center gap-2">
        <div className="w-12 h-12 rounded-2xl bg-brand-600 flex items-center justify-center shadow-lg glow-primary">
          <Film className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-black text-white mt-1">Create Account</h1>
        <p className="text-xs text-zinc-500">Sign up and get instant access to premium tickets.</p>
      </div>

      {step === 1 ? (
        /* STEP 1: Registration form */
        <form onSubmit={handleRegisterSubmit} className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex flex-col gap-4">
          {error && (
            <div className="bg-red-950/20 border border-red-500/30 text-red-400 p-3 rounded-lg text-xs flex gap-2 items-start">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Name */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="text"
                required
                placeholder="Jane Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-brand-500 text-zinc-200"
              />
            </div>
          </div>

          {/* Email */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="email"
                required
                placeholder="name@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-brand-500 text-zinc-200"
              />
            </div>
          </div>

          {/* Password */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-brand-500 text-zinc-200"
              />
            </div>
          </div>

          {/* Confirm Password */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Confirm Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-brand-500 text-zinc-200"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
          >
            {loading ? <span>Creating Account...</span> : <span>Register</span>}
          </button>

          <p className="text-xs text-zinc-500 text-center mt-2">
            Already have an account?{" "}
            <Link href={`/login?redirect=${encodeURIComponent(redirectUrl)}`} className="text-brand-400 hover:text-brand-300 font-bold">
              Sign In
            </Link>
          </p>
        </form>
      ) : (
        /* STEP 2: OTP Verification form */
        <form onSubmit={handleVerifyOtp} className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex flex-col gap-4">
          {successMsg && (
            <div className="bg-emerald-950/20 border border-emerald-500/30 text-emerald-400 p-3 rounded-lg text-xs flex gap-2 items-start">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {error && (
            <div className="bg-red-950/20 border border-red-500/30 text-red-400 p-3 rounded-lg text-xs flex gap-2 items-start">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Verification OTP Code</label>
            </div>
            <input
              type="text"
              required
              placeholder="e.g. 123456"
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              className="w-full text-center bg-zinc-950 border border-zinc-800 rounded-lg py-3 text-lg font-bold tracking-widest focus:outline-none focus:border-brand-500 text-zinc-200"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
          >
            {loading ? <span>Verifying OTP...</span> : <span>Verify & Continue</span>}
          </button>
        </form>
      )}
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={
      <div className="max-w-md mx-auto px-4 py-16 w-full flex flex-col gap-6">
        <Skeleton className="h-10 w-24 mx-auto" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    }>
      <RegisterContent />
    </Suspense>
  );
}
