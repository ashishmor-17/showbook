"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../store/useAuthStore";
import { bookingApi } from "../../lib/api";
import { Compass, Ticket, Calendar, Clock, Armchair, ChevronRight } from "lucide-react";
import { Skeleton } from "../../components/ui/Skeleton";

export default function BookingsPage() {
  const router = useRouter();
  const { user, hydrate, isHydrated } = useAuthStore();
  const [bookings, setBookings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"upcoming" | "past">("upcoming");

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (isHydrated && !user) {
      router.push("/login?redirect=/bookings");
      return;
    }

    if (user) {
      setLoading(true);
      bookingApi.list({ limit: 50 })
        .then((res) => {
          setBookings(res.data.data?.bookings || res.data?.bookings || []);
        })
        .catch((err) => console.error("Error fetching bookings list", err))
        .finally(() => setLoading(false));
    }
  }, [user, isHydrated]);

  // Group or filter bookings
  const getFilteredBookings = () => {
    // SAGA statuses: PENDING, CONFIRMED, CANCELLED, TIMED_OUT, etc.
    if (activeTab === "upcoming") {
      return bookings.filter((b) => b.status === "CONFIRMED" || b.status === "PENDING");
    } else {
      return bookings.filter((b) => b.status !== "CONFIRMED" && b.status !== "PENDING");
    }
  };

  const filtered = getFilteredBookings();

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 md:px-8 py-6 w-full flex flex-col gap-6">
        <Skeleton className="h-8 w-48" />
        <div className="flex gap-4 border-b border-zinc-800 pb-2">
          <Skeleton className="h-10 w-24 rounded-lg" />
          <Skeleton className="h-10 w-24 rounded-lg" />
        </div>
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-32 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 md:px-8 py-6 flex flex-col gap-6 w-full text-left">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">My Bookings</h1>
        <p className="text-xs text-zinc-500">View and manage your current ticket orders and past cinema receipts.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-zinc-800 pb-1">
        <button
          onClick={() => setActiveTab("upcoming")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === "upcoming"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          Upcoming Shows
        </button>
        <button
          onClick={() => setActiveTab("past")}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === "past"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          History / Past
        </button>
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center gap-4 bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
          <Ticket className="w-12 h-12 text-zinc-600" />
          <div>
            <h3 className="text-base font-bold text-white">No Tickets Found</h3>
            <p className="text-xs text-zinc-500 mt-1">
              You do not have any tickets in this section. Browse the lobby to book some!
            </p>
          </div>
          <Link
            href="/"
            className="mt-2 px-5 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs transition flex items-center gap-1"
          >
            <Compass className="w-4 h-4" />
            <span>Go to Movie Lobby</span>
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {filtered.map((b) => {
            const isConfirmed = b.status === "CONFIRMED";
            const isPending = b.status === "PENDING";
            const isExpired = b.status === "TIMED_OUT" || b.status === "FAILED";
            
            let statusColor = "bg-zinc-800/80 text-zinc-400 border-zinc-700/50";
            if (isConfirmed) statusColor = "bg-emerald-950/20 text-emerald-400 border-emerald-500/30";
            if (isPending) statusColor = "bg-amber-950/20 text-amber-400 border-amber-500/30";
            if (isExpired) statusColor = "bg-red-950/20 text-red-400 border-red-500/30";

            return (
              <Link
                key={b.booking_ref}
                href={isPending ? `/booking/${b.booking_ref}` : `/booking/success?ref=${b.booking_ref}`}
                className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 hover:border-zinc-700 transition flex flex-col sm:flex-row justify-between sm:items-center gap-4 text-sm"
              >
                {/* Details */}
                <div className="flex flex-col gap-3 text-left">
                  <div className="flex flex-col gap-1">
                    <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-wider">
                      Reference Segment: {b.booking_ref}
                    </span>
                    <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                      <span>ShowBook Cinema Event</span>
                    </h3>
                  </div>

                  <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-zinc-400 font-medium">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-brand-400" />
                      <span>{b.show_date || "Showtime Event"}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Armchair className="w-3.5 h-3.5 text-brand-400" />
                      <span>Seats: {b.seat_codes?.join(", ")}</span>
                    </div>
                  </div>
                </div>

                {/* Status / Link */}
                <div className="flex items-center justify-between sm:justify-end gap-4 border-t border-zinc-800 sm:border-0 pt-3 sm:pt-0">
                  <div className="flex flex-col sm:items-end">
                    <span className="text-[10px] text-zinc-500 font-bold">Billing Total</span>
                    <span className="text-sm font-black text-white">₹{(b.final_amount ?? (b.final_amount_paise ? b.final_amount_paise / 100.0 : 0)).toFixed(2)}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold border uppercase tracking-wider ${statusColor}`}>
                      {b.status}
                    </span>
                    <ChevronRight className="w-4 h-4 text-zinc-500 hidden sm:block" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
