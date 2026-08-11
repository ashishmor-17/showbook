"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "../../../store/useAuthStore";
import { authApi, userApi } from "../../../lib/api";
import { Lock, Mail, Film, AlertCircle } from "lucide-react";
import { Skeleton } from "../../../components/ui/Skeleton";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get("redirect") || "/";

  const { setTokens, setUser, hydrate } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.login({ email, password });
      const { access_token, refresh_token } = res.data;
      
      setTokens(access_token, refresh_token);
      
      // Fetch user profile details using the newly set token
      const profileRes = await userApi.getProfile();
      const profile = profileRes.data;
      
      setUser({
        id: profile.user_id,
        email: profile.email,
        name: profile.name || profile.email.split("@")[0],
      });
      
      router.push(redirectUrl);
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.error?.message || 
        "Invalid credentials or email not verified. Please check and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-16 flex flex-col gap-6 w-full text-left my-auto">
      {/* Brand Header */}
      <div className="flex flex-col items-center text-center gap-2">
        <div className="w-12 h-12 rounded-2xl bg-brand-600 flex items-center justify-center shadow-lg glow-primary">
          <Film className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-black text-white mt-1">Welcome to ShowBook</h1>
        <p className="text-xs text-zinc-500">Sign in to book tickets, view orders, and manage preferences.</p>
      </div>

      {/* Login Card Form */}
      <form onSubmit={handleSubmit} className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex flex-col gap-4">
        {error && (
          <div className="bg-red-950/20 border border-red-500/30 text-red-400 p-3 rounded-lg text-xs flex gap-2 items-start">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

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
          <div className="flex justify-between items-center">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Password</label>
            <span className="text-[10px] text-zinc-500 cursor-pointer hover:text-zinc-400 font-semibold">Forgot?</span>
          </div>
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

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
        >
          {loading ? <span>Signing In...</span> : <span>Sign In</span>}
        </button>

        {/* Footer link */}
        <p className="text-xs text-zinc-500 text-center mt-2">
          New to ShowBook?{" "}
          <Link href={`/register?redirect=${encodeURIComponent(redirectUrl)}`} className="text-brand-400 hover:text-brand-300 font-bold">
            Create an Account
          </Link>
        </p>
      </form>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="max-w-md mx-auto px-4 py-16 w-full flex flex-col gap-6">
        <Skeleton className="h-10 w-24 mx-auto" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    }>
      <LoginContent />
    </Suspense>
  );
}
