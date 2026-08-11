"use client";

import React from "react";
import { Filter, X } from "lucide-react";

interface FiltersProps {
  selectedLanguage: string;
  setSelectedLanguage: (lang: string) => void;
  selectedGenre: string;
  setSelectedGenre: (genre: string) => void;
  selectedDate: string;
  setSelectedDate: (date: string) => void;
}

const LANGUAGES = [
  { label: "All Languages", value: "" },
  { label: "English", value: "English" },
  { label: "Hindi", value: "Hindi" },
  { label: "Telugu", value: "Telugu" },
  { label: "Tamil", value: "Tamil" },
  { label: "Spanish", value: "Spanish" },
];

const GENRES = [
  { label: "All Genres", value: "" },
  { label: "Action", value: "Action" },
  { label: "Adventure", value: "Adventure" },
  { label: "Drama", value: "Drama" },
  { label: "Comedy", value: "Comedy" },
  { label: "Sci-Fi", value: "Sci-Fi" },
  { label: "Thriller", value: "Thriller" },
];

export default function MovieFilters({
  selectedLanguage,
  setSelectedLanguage,
  selectedGenre,
  setSelectedGenre,
  selectedDate,
  setSelectedDate,
}: FiltersProps) {
  // Generate next 5 dates for display
  const getDates = () => {
    const list = [{ label: "All Dates", value: "" }];
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

  const handleClearAll = () => {
    setSelectedLanguage("");
    setSelectedGenre("");
    setSelectedDate("");
  };

  const isAnyFilterActive = selectedLanguage || selectedGenre || selectedDate;

  return (
    <div className="flex flex-col gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-white font-medium text-sm">
          <Filter className="w-4 h-4 text-brand-400" />
          <span>Quick Filters</span>
        </div>
        {isAnyFilterActive && (
          <button
            onClick={handleClearAll}
            className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 font-semibold"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Language Filter */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-zinc-400">Language</label>
          <select
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-sm focus:outline-none focus:border-brand-500 text-zinc-300"
          >
            {LANGUAGES.map((l) => (
              <option key={l.value} value={l.value}>
                {l.label}
              </option>
            ))}
          </select>
        </div>

        {/* Genre Filter */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-zinc-400">Genre</label>
          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-sm focus:outline-none focus:border-brand-500 text-zinc-300"
          >
            {GENRES.map((g) => (
              <option key={g.value} value={g.value}>
                {g.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date Filter */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-semibold text-zinc-400">Show Date</label>
          <select
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-sm focus:outline-none focus:border-brand-500 text-zinc-300"
          >
            {dates.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
