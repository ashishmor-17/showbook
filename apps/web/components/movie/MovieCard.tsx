"use client";

import React from "react";
import Link from "next/link";
import { Star, Clock } from "lucide-react";

export interface Movie {
  id: string;
  title: string;
  slug: string;
  description?: string;
  poster_url?: string;
  language?: string;
  genre?: string[];
  rating?: number | string;
  duration_minutes?: number;
}

export default function MovieCard({ movie }: { movie: Movie }) {
  // Use a fallback image if poster_url is missing
  const poster = movie.poster_url || "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60";
  
  return (
    <Link href={`/movies/${movie.slug}`} className="group flex flex-col bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-brand-500 transition-all duration-300 transform hover:-translate-y-1 shadow-md hover:shadow-xl">
      {/* Poster area */}
      <div className="relative aspect-[2/3] w-full overflow-hidden bg-zinc-950">
        <img
          src={poster}
          alt={movie.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        {/* Hover overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60 group-hover:opacity-85 transition-opacity" />
        
        {/* Rating and Duration badge */}
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-xs font-semibold text-white">
          <div className="flex items-center gap-1 bg-black/75 px-2 py-1 rounded backdrop-blur-sm border border-zinc-700">
            <Star className="w-3.5 h-3.5 text-accent-gold fill-accent-gold" />
            <span>{movie.rating || "8.5"}</span>
          </div>
          {movie.duration_minutes && (
            <div className="flex items-center gap-1 bg-black/75 px-2 py-1 rounded backdrop-blur-sm border border-zinc-700">
              <Clock className="w-3.5 h-3.5 text-brand-400" />
              <span>{movie.duration_minutes}m</span>
            </div>
          )}
        </div>
      </div>

      {/* Movie Meta Content */}
      <div className="p-4 flex flex-col gap-2 flex-grow justify-between">
        <div>
          <h3 className="font-semibold text-white group-hover:text-brand-400 transition line-clamp-1">
            {movie.title}
          </h3>
          <span className="text-xs text-zinc-500 font-medium">
            {movie.language || "English"}
          </span>
        </div>

        {/* Genres */}
        {movie.genre && movie.genre.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {movie.genre.slice(0, 2).map((g, idx) => (
              <span
                key={idx}
                className="px-1.5 py-0.5 rounded text-[10px] bg-zinc-800 border border-zinc-700/50 text-zinc-400 font-medium"
              >
                {g}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
