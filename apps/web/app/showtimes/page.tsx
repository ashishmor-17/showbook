"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "../../store/useAuthStore";
import { venueApi } from "../../lib/api";
import { Calendar, MapPin, Film, ChevronRight, AlertCircle, RefreshCw } from "lucide-react";
import { Skeleton } from "../../components/ui/Skeleton";

interface Showtime {
  showtime_id: string;
  screen_name: string;
  screen_type: string;
  start_time: string;
  end_time: string;
  language: string;
  format: string;
  status: string;
  available_seats: number;
}

interface VenueShowtimes {
  venue_id: string;
  venue_name: string;
  shows: Showtime[];
}

function ShowtimesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const movieId = searchParams.get("movie");
  const movieTitle = searchParams.get("title") || "Movie";
  
  const { selectedCity, hydrate } = useAuthStore();
  const [selectedDate, setSelectedDate] = useState("");
  const [venues, setVenues] = useState<VenueShowtimes[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generate next 5 dates for display
  const getDates = () => {
    const list = [];
    const today = new Date();
    for (let i = 0; i < 5; i++) {
      const d = new Date();
      d.setDate(today.getDate() + i);
      const iso = d.toISOString().split("T")[0];
      
      let label = "";
      if (i === 0) label = "Today";
      else if (i === 1) label = "Tomorrow";
      else {
        label = d.toLocaleDateString("en-US", { weekday: "short", day: "numeric", month: "short" });
      }
      list.push({ label, value: iso });
    }
    return list;
  };

  const dates = getDates();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    // Default to today
    if (dates.length > 0 && !selectedDate) {
      setSelectedDate(dates[0].value);
    }
  }, [dates, selectedDate]);

  const fetchShowtimes = async () => {
    if (!movieId || !selectedCity?.id || !selectedDate) return;
    
    setLoading(true);
    setError(null);
    try {
      const res = await venueApi.getShowtimes({
        catalog_ref_id: movieId,
        catalog_type: "MOVIE",
        city_id: selectedCity.id,
        date: selectedDate,
      });
      setVenues(res.data?.showtimes || []);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch showtimes for the selected date.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShowtimes();
  }, [movieId, selectedCity, selectedDate]);

  if (!movieId) {
    return (
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-20 text-center flex flex-col items-center gap-4">
        <AlertCircle className="w-12 h-12 text-zinc-600" />
        <h3 className="text-xl font-bold text-white">Invalid Showtime Request</h3>
        <p className="text-sm text-zinc-500">Please select a movie from the catalog first.</p>
        <Link href="/" className="px-5 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 transition">
          Back to Catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 flex flex-col gap-6 w-full text-left">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-1 text-xs font-semibold text-zinc-400">
          <Link href="/" className="hover:text-white transition">Home</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-zinc-300">Showtimes</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white flex flex-col md:flex-row md:items-center gap-2 mt-1">
          <span>{movieTitle}</span>
          <span className="text-zinc-500 text-lg hidden md:inline">|</span>
          <span className="text-zinc-400 text-lg font-medium flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-brand-400" />
            {selectedCity?.name || "Loading City..."}
          </span>
        </h1>
      </div>

      {/* Date Bar */}
      <div className="flex gap-2 overflow-x-auto pb-2 border-b border-zinc-800">
        {dates.map((d) => (
          <button
            key={d.value}
            onClick={() => setSelectedDate(d.value)}
            className={`flex-shrink-0 px-5 py-3 rounded-xl border transition text-left flex flex-col gap-0.5 min-w-[100px] ${
              selectedDate === d.value
                ? "bg-brand-600 border-brand-500 text-white shadow-lg glow-primary"
                : "bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700"
            }`}
          >
            <span className="text-[10px] font-semibold uppercase tracking-wider opacity-85">
              {d.label}
            </span>
            <span className="text-sm font-bold">
              {d.value ? d.value.split("-")[2] + " " + new Date(d.value).toLocaleDateString("en-US", { month: "short" }) : "Any"}
            </span>
          </button>
        ))}
      </div>

      {/* Venues & Showtimes List */}
      {loading ? (
        <div className="flex flex-col gap-4 mt-2">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl flex flex-col gap-4">
              <Skeleton className="h-6 w-1/4" />
              <div className="flex gap-3">
                <Skeleton className="h-10 w-20 rounded-lg" />
                <Skeleton className="h-10 w-20 rounded-lg" />
                <Skeleton className="h-10 w-20 rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <p className="text-red-400 font-medium">{error}</p>
          <button
            onClick={fetchShowtimes}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-950 border border-zinc-800 hover:bg-zinc-900 transition text-sm text-zinc-300"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      ) : venues.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center gap-3 bg-zinc-900 border border-zinc-800 rounded-xl p-8">
          <AlertCircle className="w-10 h-10 text-zinc-500" />
          <h3 className="text-base font-bold text-white">No Showtimes Available</h3>
          <p className="text-xs text-zinc-500 max-w-xs">
            There are no active showtimes for this movie in your selected city on this date. Try changing the date or city.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4 mt-2">
          {venues.map((venue) => (
            <div
              key={venue.venue_id}
              className="bg-zinc-900 border border-zinc-800 p-6 rounded-xl flex flex-col md:flex-row justify-between md:items-center gap-4 hover:border-zinc-700/80 transition"
            >
              {/* Venue details */}
              <div className="flex flex-col gap-1 text-left max-w-sm">
                <h3 className="font-bold text-white text-base md:text-lg">
                  {venue.venue_name}
                </h3>
                <span className="text-xs text-zinc-500">
                  Multiple screen sizes and premium sound setups
                </span>
              </div>

              {/* Showtimes list */}
              <div className="flex flex-wrap gap-3">
                {venue.shows.map((show) => {
                  const isClosed = show.status === "CLOSED" || show.status === "CANCELLED";
                  return (
                    <Link
                      key={show.showtime_id}
                      href={isClosed ? "#" : `/seats/${show.showtime_id}`}
                      className={`flex flex-col items-center justify-center border px-4 py-2.5 rounded-xl transition text-center min-w-[90px] ${
                        isClosed
                          ? "bg-zinc-950 border-zinc-900 text-zinc-700 cursor-not-allowed pointer-events-none"
                          : "bg-zinc-950 border-zinc-800 hover:border-brand-500 text-white"
                      }`}
                    >
                      <span className="text-sm font-black">{show.start_time}</span>
                      <span className="text-[9px] text-zinc-500 font-bold mt-0.5">
                        {show.screen_type}
                      </span>
                      {show.available_seats > 0 && (
                        <span className="text-[8px] text-emerald-400 font-semibold mt-0.5">
                          {show.available_seats} left
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ShowtimesPage() {
  return (
    <Suspense fallback={
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 w-full flex flex-col gap-6">
        <div className="h-6 w-48 bg-zinc-900 rounded animate-pulse" />
        <div className="h-10 w-64 bg-zinc-900 rounded animate-pulse" />
        <div className="h-16 bg-zinc-900 rounded-xl animate-pulse" />
        <div className="h-40 bg-zinc-900 rounded-xl animate-pulse" />
      </div>
    }>
      <ShowtimesContent />
    </Suspense>
  );
}
