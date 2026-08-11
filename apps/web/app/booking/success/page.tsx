"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "../../../store/useAuthStore";
import { useBookingStore } from "../../../store/useBookingStore";
import { bookingApi } from "../../../lib/api";
import { CheckCircle2, Ticket, Printer, Share2, Compass, MapPin, Calendar, Clock, Armchair } from "lucide-react";
import { Skeleton } from "../../../components/ui/Skeleton";

function SuccessContent() {
  const searchParams = useSearchParams();
  const bookingRef = searchParams.get("ref");
  
  const { hydrate } = useAuthStore();
  const bookingStore = useBookingStore();
  
  const [booking, setBooking] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const loadBooking = async () => {
    if (!bookingRef) return;
    setLoading(true);
    try {
      const res = await bookingApi.get(bookingRef);
      setBooking(res.data.data || res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to verify final booking state.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBooking();
  }, [bookingRef]);

  if (!bookingRef) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center flex flex-col items-center gap-4">
        <h3 className="text-xl font-bold text-white">No Reference Provided</h3>
        <Link href="/" className="px-5 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
          Return Home
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 flex flex-col gap-6 w-full">
        <Skeleton className="h-10 w-1/2 mx-auto" />
        <Skeleton className="h-[450px] w-full rounded-3xl" />
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-4 py-10 flex flex-col gap-6 w-full text-center">
      {/* Success banner */}
      <div className="flex flex-col items-center gap-2">
        <CheckCircle2 className="w-16 h-16 text-accent-emerald animate-bounce" />
        <h1 className="text-2xl font-black text-white">Ticket Confirmed!</h1>
        <p className="text-sm text-zinc-400">Your booking is fully verified and confirmed in system ledger.</p>
      </div>

      {/* Premium Ticket Stub */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl overflow-hidden shadow-2xl relative">
        {/* Top header strip */}
        <div className="bg-brand-600 px-6 py-4 flex justify-between items-center text-white">
          <div className="flex items-center gap-1.5 font-bold tracking-wider text-sm">
            <Ticket className="w-4 h-4" />
            <span>SHOWBOOK ENTRY</span>
          </div>
          <span className="text-xs font-mono bg-black/25 px-2.5 py-0.5 rounded-full border border-white/10">
            {bookingRef}
          </span>
        </div>

        {/* Details section */}
        <div className="p-6 flex flex-col gap-5 text-left">
          {/* Movie title */}
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Movie Event</span>
            <h2 className="text-xl font-black text-white leading-tight">
              {bookingStore.movieTitle || "Confirmed Booking"}
            </h2>
          </div>

          <hr className="border-zinc-800 border-dashed" />

          {/* Grid fields */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="flex flex-col gap-0.5">
              <span className="text-zinc-500 font-semibold flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-brand-400" />
                <span>Venue</span>
              </span>
              <span className="text-zinc-200 font-bold">{bookingStore.venueName || "ShowBook Theater"}</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-zinc-500 font-semibold flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-brand-400" />
                <span>Show Date</span>
              </span>
              <span className="text-zinc-200 font-bold">{bookingStore.showDate || "Today"}</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-zinc-500 font-semibold flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-brand-400" />
                <span>Timing</span>
              </span>
              <span className="text-zinc-200 font-bold">{bookingStore.startTime || "10:00"}</span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-zinc-500 font-semibold flex items-center gap-1">
                <Armchair className="w-3.5 h-3.5 text-brand-400" />
                <span>Seat Codes</span>
              </span>
              <span className="text-brand-400 font-black">{booking?.seat_codes?.join(", ")}</span>
            </div>
          </div>

          <hr className="border-zinc-800 border-dashed" />

          {/* Custom QR Code SVG */}
          <div className="flex flex-col items-center gap-2 pt-2">
            <div className="bg-white p-3 rounded-2xl w-36 h-36 flex items-center justify-center shadow-lg border border-zinc-200">
              <svg
                viewBox="0 0 100 100"
                className="w-full h-full text-black"
                shapeRendering="crispEdges"
              >
                {/* Visual Mock of detailed QR grid pattern */}
                <path fill="currentColor" d="M0 0h30v30H0zm70 0h30v30H70zM0 70h30v30H0zm40 40h10v10H40zm10-20h10v10H50z" />
                <path fill="currentColor" d="M10 10h10v10H10zm70 0h10v10H80zM10 80h10v10H10zm30-40h20v20H40zm30 10h10v10H70zm20 10h10v10H90zm-10 10h10v10H80z" />
                <path fill="currentColor" d="M35 15h10v10H35zm0 20h10v10H35zm20-20h10v10H55zM15 45h10v10H15zm45 40h10v10H60zm15-45h10v10H75z" />
              </svg>
            </div>
            <span className="text-[10px] text-zinc-500 font-mono tracking-widest uppercase mt-1">
              Ref: {bookingRef}
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={() => window.print()}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 text-sm font-semibold transition"
        >
          <Printer className="w-4 h-4" />
          <span>Print Ticket</span>
        </button>
        <button
          onClick={() => alert("Copied booking reference link to clipboard!")}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 text-zinc-300 text-sm font-semibold transition"
        >
          <Share2 className="w-4 h-4" />
          <span>Share Ticket</span>
        </button>
      </div>

      <Link
        href="/"
        className="text-sm font-semibold text-brand-400 hover:text-brand-300 mt-2 flex items-center gap-1 justify-center transition"
      >
        <Compass className="w-4 h-4" />
        <span>Return to Movies Lobby</span>
      </Link>
    </div>
  );
}

export default function BookingSuccessPage() {
  return (
    <Suspense fallback={
      <div className="max-w-md mx-auto px-4 py-10 w-full flex flex-col gap-6">
        <Skeleton className="h-10 w-1/2 mx-auto" />
        <Skeleton className="h-[400px] w-full rounded-2xl" />
      </div>
    }>
      <SuccessContent />
    </Suspense>
  );
}
