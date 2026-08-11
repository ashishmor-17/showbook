"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../../store/useAuthStore";
import { useBookingStore } from "../../../store/useBookingStore";
import { bookingApi } from "../../../lib/api";
import { ChevronRight, CreditCard, Shield, Clock, Film, Ticket, Info } from "lucide-react";
import { Skeleton } from "../../../components/ui/Skeleton";

interface BookingSummaryPageProps {
  params: Promise<{ bookingId: string }>;
}

export default function BookingSummaryPage({ params }: BookingSummaryPageProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const bookingRef = resolvedParams.bookingId;

  const { user, hydrate } = useAuthStore();
  const bookingStore = useBookingStore();

  const [booking, setBooking] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const loadBooking = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await bookingApi.get(bookingRef);
      setBooking(res.data.data || res.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch booking invoice. It may have expired.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBooking();
  }, [bookingRef]);

  if (loading) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 flex flex-col gap-6 w-full">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-[400px] w-full rounded-2xl" />
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center flex flex-col items-center gap-4">
        <Info className="w-12 h-12 text-zinc-600" />
        <h3 className="text-xl font-bold text-white">Booking Not Found</h3>
        <p className="text-sm text-zinc-500">{error || "This invoice does not exist or has expired."}</p>
        <Link href="/" className="px-5 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 transition">
          Back to Catalog
        </Link>
      </div>
    );
  }

  // SAGA statuses: PENDING, CONFIRMED, CANCELLED, FAILED, TIMED_OUT, INITIATED...
  const isExpired = booking.status === "TIMED_OUT" || booking.status === "FAILED" || booking.status === "CANCELLED";

  // Calculate prices
  const finalAmount = booking.final_amount ?? (booking.final_amount_paise ? booking.final_amount_paise / 100.0 : 0);
  const amountPaiseVal = booking.final_amount_paise ?? (booking.final_amount ? Math.round(booking.final_amount * 100) : 0);
  const basePrice = finalAmount - 20 - (finalAmount * 0.18); // fallback estimate
  
  // Taxes and convenience fee
  const convenienceFee = 20.0; // ₹20
  const gst = 3.6; // 18% of ₹20
  const ticketCost = finalAmount - convenienceFee - gst;

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 flex flex-col gap-6 w-full text-left">
      {/* Header */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-1 text-xs font-semibold text-zinc-400">
          <Link href="/" className="hover:text-white transition">Home</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-zinc-300">Checkout Summary</span>
        </div>
        <h1 className="text-xl md:text-2xl font-black text-white">Booking Invoice</h1>
        <p className="text-xs text-zinc-500">Invoice: {booking.booking_ref}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left/Middle: Ticket Summary */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Movie details card */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col sm:flex-row gap-6 hover:border-zinc-700 transition">
            <div className="flex flex-col gap-4 flex-grow text-left">
              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] font-semibold text-brand-400 uppercase tracking-wider">You are watching</span>
                <h2 className="text-2xl font-black text-white">{bookingStore.movieTitle || "Movie Event"}</h2>
              </div>
              <hr className="border-zinc-850" />
              <div className="grid grid-cols-2 gap-y-4 gap-x-2 text-sm text-zinc-300">
                <div className="flex flex-col">
                  <span className="text-xs text-zinc-500">Theater / Venue</span>
                  <span className="font-semibold">{bookingStore.venueName || "ShowBook screen"}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-zinc-500">Show Time</span>
                  <span className="font-semibold">{bookingStore.showDate || "Today"} | {bookingStore.startTime || "10:00"}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-zinc-500">Seats Locked</span>
                  <span className="font-semibold text-brand-400">{booking.seat_codes?.join(", ")}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-zinc-500">Booking Status</span>
                  <span className={`font-semibold uppercase ${isExpired ? "text-red-400" : "text-amber-400"}`}>
                    {booking.status}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Policy notes */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 flex gap-3 items-start text-xs text-zinc-400">
            <Shield className="w-5 h-5 text-brand-400 flex-shrink-0 mt-0.5" />
            <div className="flex flex-col gap-1">
              <span className="font-bold text-zinc-300">Cancellation Policy</span>
              <p className="leading-relaxed">
                Tickets can be cancelled up to 2 hours prior to the show start time. A refund will be initiated to your original payment method. Cancellation is not available within the 2-hour window.
              </p>
            </div>
          </div>
        </div>

        {/* Right: Payment invoice details */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col gap-4 text-sm relative overflow-hidden">
            <h3 className="font-bold text-white uppercase text-xs tracking-wider border-b border-zinc-800 pb-3">
              Payment Breakdown
            </h3>

            {/* List */}
            <div className="flex flex-col gap-3 text-zinc-300">
              <div className="flex justify-between items-center">
                <span>Ticket Subtotal ({booking.seat_codes?.length || 1} Seats)</span>
                <span>₹{ticketCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="flex items-center gap-1">
                  <span>Convenience Fee</span>
                </span>
                <span>₹{convenienceFee.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center border-b border-zinc-850 pb-3">
                <span className="flex items-center gap-1">
                  <span>GST (18%)</span>
                </span>
                <span>₹{gst.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-white font-extrabold text-base pt-1">
                <span>Total Amount</span>
                <span className="text-brand-400">₹{finalAmount.toFixed(2)}</span>
              </div>
            </div>

            {/* Button */}
            {isExpired ? (
              <div className="w-full text-center py-3.5 rounded-xl bg-zinc-800 text-zinc-500 font-extrabold text-sm border border-zinc-700/50">
                Invoice Expired
              </div>
            ) : (
              <Link
                href={`/payment?booking_ref=${booking.booking_ref}&amount=${amountPaiseVal}`}
                className="w-full text-center py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
              >
                <CreditCard className="w-4 h-4" />
                <span>Proceed to Payment</span>
              </Link>
            )}

            {/* Safety badge */}
            <div className="text-[10px] text-zinc-500 text-center mt-2 flex items-center justify-center gap-1">
              <Clock className="w-3 h-3" />
              <span>Complete payment before session timer expires.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
