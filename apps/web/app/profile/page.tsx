"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../store/useAuthStore";
import { authApi } from "../../lib/api";
import { User, Mail, ShieldCheck, MapPin, Save, Settings, LogOut } from "lucide-react";
import { Skeleton } from "../../components/ui/Skeleton";

export default function ProfilePage() {
  const router = useRouter();
  const { user, selectedCity, hydrate, isHydrated, logout } = useAuthStore();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (isHydrated && !user) {
      router.push("/login?redirect=/profile");
      return;
    }

    if (user) {
      setName(user.name);
      setEmail(user.email);
    }
  }, [user, isHydrated]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate updating profile details
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    }, 1000);
  };

  if (loading && !name) {
    return (
      <div className="max-w-xl mx-auto px-4 py-12 flex flex-col gap-6 w-full">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-48 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-10 flex flex-col gap-6 w-full text-left">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-brand-500" />
            <span>Profile Dashboard</span>
          </h1>
          <p className="text-xs text-zinc-500">Configure your user information and regional booking preferences.</p>
        </div>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-red-400 text-xs font-semibold flex items-center gap-1.5 transition"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Logout</span>
        </button>
      </div>

      {/* Profile Card */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col gap-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-brand-600 flex items-center justify-center text-2xl font-black text-white border border-brand-500 shadow-lg glow-primary">
            {name ? String(name).charAt(0).toUpperCase() : "U"}
          </div>
          <div className="flex flex-col">
            <h3 className="text-lg font-bold text-white uppercase">{name || "User Name"}</h3>
            <span className="text-xs text-zinc-500">User UID: {user?.id}</span>
          </div>
        </div>

        <hr className="border-zinc-800" />

        <form onSubmit={handleSave} className="flex flex-col gap-4">
          {success && (
            <div className="bg-emerald-950/20 border border-emerald-500/30 text-emerald-400 p-3 rounded-lg text-xs font-semibold">
              Profile settings updated successfully!
            </div>
          )}

          {/* Name field */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-brand-500 text-zinc-200"
              />
            </div>
          </div>

          {/* Email field */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="email"
                disabled
                value={email}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none text-zinc-500 cursor-not-allowed"
              />
            </div>
          </div>

          {/* Preferred City field */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Preferred City</label>
            <div className="relative">
              <MapPin className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="text"
                disabled
                value={selectedCity?.name || "None Selected"}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm focus:outline-none text-zinc-500 cursor-not-allowed"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
          >
            <Save className="w-4 h-4" />
            <span>{loading ? "Saving Changes..." : "Save Preferences"}</span>
          </button>
        </form>
      </div>

      {/* Security note */}
      <div className="flex items-center gap-2 justify-center text-[10px] text-zinc-500">
        <ShieldCheck className="w-4 h-4 text-brand-400" />
        <span>Authentication session tokens expire automatically.</span>
      </div>
    </div>
  );
}
