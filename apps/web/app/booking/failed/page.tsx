"use client";

import React, { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { XCircle, RefreshCw, HelpCircle, Compass } from "lucide-react";

function FailedContent() {
  const searchParams = useSearchParams();
  const bookingRef = searchParams.get("ref");

  return (
    <div className="max-w-md mx-auto px-4 py-16 flex flex-col gap-6 w-full text-center items-center justify-center my-auto">
      <XCircle className="w-16 h-16 text-red-500 animate-pulse" />
      
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-black text-white">Payment Failed</h1>
        <p className="text-sm text-zinc-400">
          The transaction could not be processed by the payment gateway or the seat lock timer expired.
        </p>
        {bookingRef && (
          <span className="text-xs text-zinc-500 font-mono mt-1">Invoice Ref: {bookingRef}</span>
        )}
      </div>

      <div className="flex flex-col gap-3 w-full mt-4">
        {bookingRef ? (
          <Link
            href={`/booking/${bookingRef}`}
            className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Booking Invoice</span>
          </Link>
        ) : (
          <Link
            href="/"
            className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
          >
            <Compass className="w-4 h-4" />
            <span>Browse Catalog Again</span>
          </Link>
        )}
        
        <Link
          href="/"
          className="w-full py-3 rounded-xl bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 transition text-sm font-bold text-zinc-300 flex items-center justify-center gap-2"
        >
          <HelpCircle className="w-4 h-4" />
          <span>Contact Support Desk</span>
        </Link>
      </div>

      <Link
        href="/"
        className="text-sm font-semibold text-brand-400 hover:text-brand-300 mt-4 transition"
      >
        Return to Home Lobby
      </Link>
    </div>
  );
}

export default function BookingFailedPage() {
  return (
    <Suspense fallback={
      <div className="max-w-md mx-auto px-4 py-16 w-full flex flex-col gap-6 text-center items-center">
        <div className="w-16 h-16 rounded-full bg-zinc-900 animate-pulse" />
        <div className="h-6 w-32 bg-zinc-900 rounded animate-pulse" />
        <div className="h-12 w-full bg-zinc-900 rounded-xl animate-pulse" />
      </div>
    }>
      <FailedContent />
    </Suspense>
  );
}
