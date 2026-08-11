"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "../store/useAuthStore";
import { catalogApi } from "../lib/api";
import MovieCard, { Movie } from "../components/movie/MovieCard";
import MovieFilters from "../components/movie/MovieFilters";
import { MovieCardSkeleton } from "../components/ui/Skeleton";
import { Film, Play, Compass, RefreshCw } from "lucide-react";

function HomeContent() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const { selectedCity } = useAuthStore();

  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedLanguage, setSelectedLanguage] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");
  const [selectedDate, setSelectedDate] = useState("");

  const fetchMovies = async () => {
    setLoading(true);
    setError(null);
    try {
      if (query) {
        // Query search endpoint
        const params: any = { q: query };
        if (selectedCity?.id) {
          params.city_id = selectedCity.id;
        }
        const res = await catalogApi.searchMovies(params);
        setMovies(res.data || []);
      } else {
        // Query default movies list
        const params: any = {};
        if (selectedLanguage) params.language = selectedLanguage;
        if (selectedGenre) params.genre = selectedGenre;
        if (selectedDate) params.release_date = selectedDate;
        if (selectedCity?.slug) params.city = selectedCity.slug;
        
        const res = await catalogApi.getMovies(params);
        setMovies(res.data?.items || []);
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch movies. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMovies();
  }, [query, selectedLanguage, selectedGenre, selectedDate, selectedCity]);

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 flex flex-col gap-8 w-full">
      {/* Hero promo banner */}
      {!query && (
        <div className="relative rounded-2xl overflow-hidden bg-gradient-to-r from-brand-950 via-zinc-900 to-zinc-950 border border-zinc-800 p-8 md:p-12 flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl glow-primary">
          <div className="flex flex-col gap-3 text-left max-w-lg">
            <span className="text-xs font-semibold text-brand-400 uppercase tracking-widest">Cinema Experience Reimagined</span>
            <h1 className="text-3xl md:text-5xl font-extrabold text-white leading-tight">
              Experience Movies in Premium Quality
            </h1>
            <p className="text-sm text-zinc-400 leading-relaxed">
              Book tickets for now showing blockbusters, enjoy high-end seat selection, and settle up securely.
            </p>
          </div>
          <div className="flex items-center justify-center w-24 h-24 rounded-full bg-brand-600/25 border border-brand-500/50 hover:scale-110 transition duration-300">
            <Play className="w-10 h-10 text-brand-400 fill-brand-400 ml-1 cursor-pointer animate-pulse-slow" />
          </div>
        </div>
      )}

      {/* Filters Section */}
      <MovieFilters
        selectedLanguage={selectedLanguage}
        setSelectedLanguage={setSelectedLanguage}
        selectedGenre={selectedGenre}
        setSelectedGenre={setSelectedGenre}
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
      />

      {/* Movie Section Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Compass className="w-5 h-5 text-brand-500" />
          <span>{query ? `Search Results for "${query}"` : "Recommended Movies"}</span>
        </h2>
        {selectedCity && (
          <span className="text-xs text-zinc-400 font-semibold bg-zinc-900 px-2.5 py-1 rounded-md border border-zinc-800">
            Now showing in {selectedCity.name}
          </span>
        )}
      </div>

      {/* Movie Cards List */}
      {loading ? (
        <div className="movie-grid">
          {Array.from({ length: 8 }).map((_, idx) => (
            <MovieCardSkeleton key={idx} />
          ))}
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
          <p className="text-red-400 font-medium">{error}</p>
          <button
            onClick={fetchMovies}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-950 border border-zinc-800 hover:bg-zinc-900 transition text-sm text-zinc-300"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      ) : movies.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center gap-4">
          <Film className="w-12 h-12 text-zinc-600" />
          <div>
            <h3 className="text-lg font-semibold text-white">No Movies Found</h3>
            <p className="text-sm text-zinc-500 mt-1">
              Try adjusting your filters or search query, or select another city.
            </p>
          </div>
        </div>
      ) : (
        <div className="movie-grid">
          {movies.map((movie) => (
            <MovieCard key={movie.id} movie={movie} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 w-full flex flex-col gap-6">
        <div className="h-40 rounded-2xl bg-zinc-900 animate-pulse border border-zinc-800" />
        <div className="h-16 rounded-xl bg-zinc-900 animate-pulse border border-zinc-800" />
        <div className="h-8 w-48 bg-zinc-900 rounded animate-pulse" />
        <div className="movie-grid">
          {Array.from({ length: 4 }).map((_, idx) => (
            <MovieCardSkeleton key={idx} />
          ))}
        </div>
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
