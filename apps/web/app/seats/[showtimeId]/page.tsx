"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../../../store/useAuthStore";
import { useBookingStore } from "../../../store/useBookingStore";
import { venueApi, bookingApi, catalogApi } from "../../../lib/api";
import { ChevronRight, Armchair, AlertCircle, ShoppingBag, ArrowRight } from "lucide-react";
import { Skeleton } from "../../../components/ui/Skeleton";

interface SeatSelectionPageProps {
  params: Promise<{ showtimeId: string }>;
}

export default function SeatSelectionPage({ params }: SeatSelectionPageProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const showtimeId = resolvedParams.showtimeId;

  const { user, isHydrated, hydrate } = useAuthStore();
  const { selectedSeats, setSelectedSeats, setBookingDetails, clearBooking } = useBookingStore();

  const [seatMap, setSeatMap] = useState<any>(null);
  const [showtimeDetails, setShowtimeDetails] = useState<any>(null);
  const [movieDetails, setMovieDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bookingLoading, setBookingLoading] = useState(false);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch seat map
      const seatMapRes = await venueApi.getSeats(showtimeId);
      setSeatMap(seatMapRes.data);

      // 2. Fetch showtime details
      const showtimeRes = await venueApi.getShowtimeDetails(showtimeId);
      setShowtimeDetails(showtimeRes.data);

      // 3. Fetch movie details
      if (showtimeRes.data?.catalog_ref_id) {
        const movieRes = await catalogApi.getMovieById(showtimeRes.data.catalog_ref_id);
        setMovieDetails(movieRes.data);
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch seat availability map.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Clear selection on page enter
    setSelectedSeats([]);
  }, [showtimeId]);

  // Handle seat toggling
  const handleSeatClick = (seatCode: string) => {
    if (selectedSeats.includes(seatCode)) {
      setSelectedSeats(selectedSeats.filter((s) => s !== seatCode));
    } else {
      // Max 10 seats per booking
      if (selectedSeats.length >= 10) {
        alert("You can select up to 10 seats only.");
        return;
      }
      setSelectedSeats([...selectedSeats, seatCode]);
    }
  };

  // Price calculations
  const getSeatPrice = (seatCode: string) => {
    if (!seatMap) return 0;
    for (const cat of seatMap.categories) {
      for (const row of cat.rows) {
        if (row.seats.some((s: any) => s.seat_code === seatCode)) {
          return cat.price_paise / 100.0;
        }
      }
    }
    return 0;
  };

  const getSubtotal = () => {
    return selectedSeats.reduce((acc, code) => acc + getSeatPrice(code), 0);
  };

  const handleContinue = async () => {
    if (!user) {
      // Redirect to login with dynamic redirect parameter
      router.push(`/login?redirect=/seats/${showtimeId}`);
      return;
    }

    if (selectedSeats.length === 0) {
      alert("Please select at least one seat.");
      return;
    }

    setBookingLoading(true);
    try {
      // Store info in Zustand booking store for checkout page
      const basePrice = getSeatPrice(selectedSeats[0]); // assume same category for ease
      setBookingDetails({
        showtimeId,
        movieTitle: movieDetails?.title || "Movie",
        venueName: showtimeDetails?.venue_name || "Theater",
        startTime: showtimeDetails?.start_time || "10:00",
        showDate: showtimeDetails?.show_date || "Today",
        pricePerSeat: basePrice,
      });

      // Initiate booking call to backend
      const idempotencyKey = `idemp-${Date.now()}`;
      const res = await bookingApi.initiate({
        showtime_id: showtimeId,
        seat_codes: selectedSeats,
        idempotency_key: idempotencyKey,
      });

      const bookingRef = res.data.data?.booking_ref || res.data.booking_ref;
      router.push(`/booking/${bookingRef}`);
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.error?.message || "Double-booking / lock conflict: Seat already locked. Try another seat.");
      // Refresh seat map
      loadData();
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 w-full flex flex-col gap-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (error || !seatMap) {
    return (
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-20 text-center flex flex-col items-center gap-4">
        <AlertCircle className="w-12 h-12 text-red-400" />
        <h3 className="text-xl font-bold text-white">Error Loading Seats</h3>
        <p className="text-sm text-zinc-500">{error || "Seat map is unavailable."}</p>
        <button onClick={loadData} className="px-5 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 transition">
          Retry
        </button>
      </div>
    );
  }

  const subtotal = getSubtotal();

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 flex flex-col gap-6 w-full text-left">
      {/* Header */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-1 text-xs font-semibold text-zinc-400">
          <Link href="/" className="hover:text-white transition">Home</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-zinc-300">Seats</span>
        </div>
        <h1 className="text-xl md:text-2xl font-black text-white">
          {movieDetails?.title || "Movie Screen"}
        </h1>
        <p className="text-xs text-zinc-400">
          {showtimeDetails?.venue_name} | {showtimeDetails?.show_date} at {showtimeDetails?.start_time} ({seatMap.screen_type})
        </p>
      </div>

      {/* Screen Curved Indicator */}
      <div className="flex flex-col items-center mt-6 w-full overflow-hidden">
        <div className="text-[10px] font-semibold text-zinc-500 uppercase tracking-[0.25em] mb-3">
          All Eyes This Way (Screen)
        </div>
        <div className="screen-curve" />
      </div>

      {/* Seating Layout Grid */}
      <div className="flex flex-col gap-8 overflow-x-auto py-8 min-h-[300px] items-center">
        {seatMap.categories.map((cat: any) => (
          <div key={cat.id} className="flex flex-col gap-3 w-full max-w-2xl">
            {/* Category header */}
            <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5 px-2">
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">{cat.name}</span>
              <span className="text-xs text-brand-400 font-semibold">₹{(cat.price_paise / 100.0).toFixed(2)}</span>
            </div>

            {/* Rows */}
            <div className="flex flex-col gap-2.5">
              {cat.rows.map((r: any) => (
                <div key={r.row} className="flex items-center gap-4">
                  {/* Row Code */}
                  <span className="w-6 text-sm font-bold text-zinc-500 text-center">{r.row}</span>
                  
                  {/* Seats map */}
                  <div className="flex flex-1 justify-center gap-2">
                    {r.seats.map((s: any) => {
                      const isBooked = s.status === "BOOKED";
                      const isLocked = s.status === "LOCKED";
                      const isSelected = selectedSeats.includes(s.seat_code);
                      
                      let seatColor = "bg-emerald-950/20 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 hover:border-emerald-400";
                      if (isBooked) seatColor = "bg-zinc-800 border-zinc-800 text-zinc-600 cursor-not-allowed";
                      if (isLocked) seatColor = "bg-amber-950/20 border-amber-500/30 text-amber-500 cursor-not-allowed";
                      if (isSelected) seatColor = "bg-brand-600 border-brand-500 text-white glow-primary";

                      return (
                        <button
                          key={s.seat_code}
                          disabled={isBooked || isLocked}
                          onClick={() => handleSeatClick(s.seat_code)}
                          className={`w-8 h-8 rounded-lg border text-[10px] font-bold transition flex items-center justify-center ${seatColor}`}
                          title={`Seat ${s.seat_code} - ${s.status}`}
                        >
                          <Armchair className="w-4 h-4" />
                        </button>
                      );
                    })}
                  </div>
                  
                  <span className="w-6 text-sm font-bold text-zinc-500 text-center">{r.row}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Legend & Summary section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center border-t border-zinc-800 pt-6">
        {/* Legend */}
        <div className="flex flex-wrap gap-4 justify-start text-xs font-semibold">
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-emerald-950/20 border border-emerald-500/30" />
            <span className="text-zinc-400">Available</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-amber-950/20 border border-amber-500/30" />
            <span className="text-zinc-400">Locked</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-zinc-800 border border-zinc-800" />
            <span className="text-zinc-400">Booked</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded bg-brand-600 border border-brand-500" />
            <span className="text-zinc-300">Selected</span>
          </div>
        </div>

        {/* Selected Seats summary */}
        <div className="flex flex-col gap-1 text-left">
          <span className="text-xs text-zinc-500 font-semibold">Selected Seats</span>
          <div className="text-sm font-bold text-white flex items-center gap-2">
            {selectedSeats.length > 0 ? (
              selectedSeats.join(", ")
            ) : (
              <span className="text-zinc-500 font-normal">None selected</span>
            )}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end gap-4 items-center">
          <div className="flex flex-col text-right">
            <span className="text-xs text-zinc-500 font-semibold">Total Price</span>
            <span className="text-lg font-black text-brand-400">₹{subtotal.toFixed(2)}</span>
          </div>
          <button
            onClick={handleContinue}
            disabled={selectedSeats.length === 0 || bookingLoading}
            className={`px-6 py-3 rounded-xl font-extrabold text-sm flex items-center gap-2 transition ${
              selectedSeats.length === 0 || bookingLoading
                ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                : "bg-brand-600 hover:bg-brand-500 text-white shadow-xl glow-primary"
            }`}
          >
            {bookingLoading ? (
              <span>Locking Seats...</span>
            ) : (
              <>
                <span>Continue</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
