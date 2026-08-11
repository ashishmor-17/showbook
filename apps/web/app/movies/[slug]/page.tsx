"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { catalogApi } from "../../../lib/api";
import { Movie } from "../../../components/movie/MovieCard";
import { Star, Clock, Calendar, Globe, Film, ChevronRight, Play } from "lucide-react";
import { Skeleton } from "../../../components/ui/Skeleton";

interface MovieDetailProps {
  params: Promise<{ slug: string }>;
}

export default function MovieDetailPage({ params }: MovieDetailProps) {
  const router = useRouter();
  const resolvedParams = use(params);
  const slug = resolvedParams.slug;

  const [movie, setMovie] = useState<Movie | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    catalogApi.getMovie(slug)
      .then((res) => {
        setMovie(res.data);
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to load movie details.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [slug]);

  if (loading) {
    return (
      <div className="flex flex-col w-full gap-8">
        <Skeleton className="h-[400px] w-full" />
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 w-full grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-1">
            <Skeleton className="aspect-[2/3] w-full rounded-xl" />
          </div>
          <div className="md:col-span-3 flex flex-col gap-4">
            <Skeleton className="h-10 w-1/3" />
            <Skeleton className="h-6 w-1/4" />
            <Skeleton className="h-24 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !movie) {
    return (
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-20 text-center flex flex-col items-center gap-4">
        <Film className="w-12 h-12 text-red-400" />
        <h3 className="text-xl font-bold text-white">Movie Not Found</h3>
        <p className="text-sm text-zinc-500">{error || "The movie slug does not exist."}</p>
        <Link href="/" className="px-5 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 transition">
          Back to Home
        </Link>
      </div>
    );
  }

  const poster = movie.poster_url || "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60";
  // Fallback banner
  const banner = (movie as any).banner_url || "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=1200&auto=format&fit=crop&q=60";

  return (
    <div className="flex flex-col w-full bg-background">
      {/* Banner / Hero Section */}
      <div className="relative h-[300px] md:h-[450px] w-full overflow-hidden">
        {/* Background Banner Image */}
        <img
          src={banner}
          alt={movie.title}
          className="w-full h-full object-cover filter blur-[2px] brightness-[0.3]"
        />
        {/* Glowing Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
        
        {/* Breadcrumbs */}
        <div className="absolute top-6 left-4 md:left-8 flex items-center gap-1.5 text-xs font-semibold text-zinc-400">
          <Link href="/" className="hover:text-white transition">Home</Link>
          <ChevronRight className="w-3.5 h-3.5" />
          <span className="text-zinc-300">{movie.title}</span>
        </div>
      </div>

      {/* Main Info Section */}
      <div className="max-w-7xl mx-auto px-4 md:px-8 pb-16 -mt-32 md:-mt-48 relative z-10 grid grid-cols-1 md:grid-cols-4 gap-8 w-full">
        {/* Left: Poster */}
        <div className="md:col-span-1 flex flex-col gap-4">
          <div className="aspect-[2/3] w-full rounded-2xl overflow-hidden border border-zinc-800 shadow-2xl bg-zinc-950">
            <img src={poster} alt={movie.title} className="w-full h-full object-cover" />
          </div>
          
          {/* Action Button */}
          <Link
            href={`/showtimes?movie=${movie.id}&title=${encodeURIComponent(movie.title)}`}
            className="w-full text-center py-3.5 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white shadow-xl glow-primary tracking-wider"
          >
            Book Tickets
          </Link>
        </div>

        {/* Right: Metadata & Synopsis */}
        <div className="md:col-span-3 flex flex-col gap-6 text-left">
          <div className="flex flex-col gap-2">
            <h1 className="text-3xl md:text-5xl font-black text-white leading-tight">
              {movie.title}
            </h1>
            
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-2">
              {/* Rating */}
              <div className="flex items-center gap-1 text-sm font-bold text-accent-gold">
                <Star className="w-4 h-4 fill-accent-gold" />
                <span>{movie.rating || "8.5"}</span>
                <span className="text-zinc-500 font-normal">/ 10</span>
              </div>
              
              <span className="text-zinc-700 font-bold">•</span>
              
              {/* Duration */}
              {movie.duration_minutes && (
                <div className="flex items-center gap-1 text-sm text-zinc-300">
                  <Clock className="w-4 h-4 text-brand-400" />
                  <span>{movie.duration_minutes} mins</span>
                </div>
              )}
              
              <span className="text-zinc-700 font-bold">•</span>

              {/* Language */}
              <div className="flex items-center gap-1 text-sm text-zinc-300">
                <Globe className="w-4 h-4 text-brand-400" />
                <span>{movie.language || "English"}</span>
              </div>
            </div>
          </div>

          {/* Genres */}
          {movie.genre && movie.genre.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {movie.genre.map((g, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-full text-xs bg-zinc-900 border border-zinc-800 text-zinc-300 font-medium"
                >
                  {g}
                </span>
              ))}
            </div>
          )}

          {/* Synopsis */}
          <div className="flex flex-col gap-2">
            <h3 className="text-lg font-bold text-white uppercase tracking-wider text-sm text-brand-400">
              Synopsis
            </h3>
            <p className="text-zinc-300 leading-relaxed text-sm">
              {movie.description || "No synopsis available for this movie."}
            </p>
          </div>

          {/* Trailer button */}
          {(movie as any).trailer_url && (
            <div className="flex mt-2">
              <a
                href={(movie as any).trailer_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 text-sm font-semibold transition"
              >
                <Play className="w-4 h-4 text-accent-rose fill-accent-rose" />
                <span>Watch Official Trailer</span>
              </a>
            </div>
          )}

          {/* Cast & Crew Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-zinc-800 pt-6 mt-4">
            {/* Cast List */}
            {((movie as any).cast && (movie as any).cast.length > 0) && (
              <div className="flex flex-col gap-3">
                <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">Cast</h4>
                <div className="flex flex-col gap-2.5">
                  {(movie as any).cast.slice(0, 4).map((actor: any, idx: number) => {
                    const name = typeof actor === "string" ? actor : actor?.name || "";
                    const role = typeof actor === "string" ? "Actor" : actor?.role || "Actor";
                    return (
                      <div key={idx} className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-bold text-zinc-400 border border-zinc-700">
                          {String(name || "").charAt(0)}
                        </div>
                        <div className="flex flex-col text-left">
                          <span className="text-sm text-zinc-300 font-medium">{name}</span>
                          {role && role !== "Actor" && (
                            <span className="text-[10px] text-zinc-500 font-semibold">{role}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Crew List */}
            {((movie as any).crew && (movie as any).crew.length > 0) && (
              <div className="flex flex-col gap-3">
                <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">Crew</h4>
                <div className="flex flex-col gap-2.5">
                  {(movie as any).crew.slice(0, 4).map((member: any, idx: number) => {
                    const name = typeof member === "string" ? member : member?.name || "";
                    const role = typeof member === "string" ? "Crew" : member?.role || "";
                    return (
                      <div key={idx} className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-bold text-zinc-400 border border-zinc-700">
                          {String(name || "").charAt(0)}
                        </div>
                        <div className="flex flex-col text-left">
                          <span className="text-sm text-zinc-300 font-medium">{name}</span>
                          {role && (
                            <span className="text-[10px] text-zinc-500 font-semibold">{role}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
